#!/usr/bin/env python3
"""
Improved RAG System for AWS Compliance Documentation
Fixes all identified issues: smart chunking, metadata extraction, hybrid search, query enhancement
"""

import chromadb
from sentence_transformers import SentenceTransformer
import os
import glob
from typing import List, Dict
import hashlib
import tiktoken
from rank_bm25 import BM25Okapi
import nltk
import re

class ImprovedRAGSystem:
    def __init__(self, persist_path=None):
        """Initialize the improved RAG system"""
        if persist_path is None:
            persist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db_improved")
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(
            name="aws_compliance_improved",
            metadata={"hnsw:space": "cosine"}
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.chunks = []
        self.chunk_data = {}
        self.bm25 = None

    def smart_chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """
        Smart chunking: sentence-aware with token counting
        """
        sentences = nltk.sent_tokenize(text)
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(self.enc.encode(sentence))
            if current_tokens + sentence_tokens > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Overlap: keep last overlap tokens worth of text
                    tokens = self.enc.encode(current_chunk)
                    if len(tokens) > overlap:
                        overlap_tokens = tokens[-overlap:]
                        overlap_text = self.enc.decode(overlap_tokens)
                        current_chunk = overlap_text
                        current_tokens = overlap
                    else:
                        current_chunk = current_chunk
                        current_tokens = len(tokens)
                else:
                    # Sentence too long, add as is
                    chunks.append(sentence.strip())
                    current_chunk = ""
                    current_tokens = 0
            else:
                current_chunk += sentence + " "
                current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def extract_metadata(self, chunk: str, file_path: str) -> Dict:
        """Extract AWS service, section, and policy IDs"""
        metadata = {
            "source": os.path.basename(file_path),
            "aws_service": [],
            "section": "",
            "policy_id": ""
        }

        # AWS services
        services = ['S3', 'EC2', 'IAM', 'RDS', 'Lambda', 'VPC', 'CloudTrail', 'EBS', 'CloudWatch',
                   'DynamoDB', 'SNS', 'SQS', 'Kinesis', 'Glue', 'Athena', 'Redshift', 'EMR', 'SageMaker']
        found_services = []
        for service in services:
            if service.lower() in chunk.lower():
                found_services.append(service)
        metadata["aws_service"] = ",".join(found_services) if found_services else ""

        # Policy ID
        policy_match = re.search(r'AWS-POL-[A-Z0-9-]+', chunk)
        if policy_match:
            metadata["policy_id"] = policy_match.group()

        # Section: look for headers
        lines = chunk.split('\n')
        for line in lines[:5]:  # Check first few lines
            if line.strip().startswith('#'):
                metadata["section"] = line.lstrip('#').strip()
                break

        return metadata

    def enhance_query(self, query: str) -> str:
        """Enhance query with acronyms and synonyms"""
        acronyms = {
            'S3': 'Simple Storage Service',
            'EC2': 'Elastic Compute Cloud',
            'IAM': 'Identity and Access Management',
            'RDS': 'Relational Database Service',
            'VPC': 'Virtual Private Cloud',
            'KMS': 'Key Management Service',
            'EBS': 'Elastic Block Store',
            'SNS': 'Simple Notification Service',
            'SQS': 'Simple Queue Service'
        }

        synonyms = {
            'encryption': ['encrypt', 'encrypted', 'cipher'],
            'security': ['secure', 'protection'],
            'logging': ['log', 'audit'],
            'tagging': ['tag', 'label'],
            'policy': ['rule', 'requirement'],
            'compliance': ['conformance', 'adherence']
        }

        enhanced = query.lower()
        for abbr, full in acronyms.items():
            if abbr.lower() in enhanced:
                enhanced += " " + full.lower()

        for key, syns in synonyms.items():
            if key in enhanced:
                enhanced += " " + " ".join(syns)

        return enhanced

    def process_documents(self, docs_path: str):
        """Process documents with improved chunking and metadata"""
        print("📚 Processing documents with improvements...")
        
        files = glob.glob(f"{docs_path}/**/*.md", recursive=True)
        files.extend(glob.glob(f"{docs_path}/**/*.txt", recursive=True))
        
        all_chunks = []
        all_embeddings = []
        all_ids = []
        all_metadatas = []
        
        for file_path in files:
            print(f"  Processing: {os.path.basename(file_path)}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Smart chunking
            chunks = self.smart_chunk_text(content, chunk_size=512, overlap=50)
            
            for i, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(f"{file_path}_{i}_{chunk[:50]}".encode()).hexdigest()
                
                # Extract metadata
                metadata = self.extract_metadata(chunk, file_path)
                
                # Generate embedding
                embedding = self.model.encode(chunk)
                
                all_chunks.append(chunk)
                all_embeddings.append(embedding.tolist())
                all_ids.append(chunk_id)
                all_metadatas.append(metadata)
                
                # Store for search
                self.chunk_data[chunk_id] = {'content': chunk, 'metadata': metadata}
        
        # Add to ChromaDB
        if all_chunks:
            self.collection.add(
                documents=all_chunks,
                embeddings=all_embeddings,
                ids=all_ids,
                metadatas=all_metadatas
            )
            print(f"✅ Added {len(all_chunks)} chunks to vector store")
        
        # Setup BM25
        self.chunks = all_chunks
        tokenized_corpus = [chunk.lower().split() for chunk in all_chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Hybrid search: 70% semantic + 30% BM25 keyword
        """
        enhanced_query = self.enhance_query(query)
        
        # Semantic search
        query_embedding = self.model.encode(enhanced_query)
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results * 3  # Get more for combining
        )
        
        # BM25 search
        query_tokens = enhanced_query.lower().split()
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # Combine scores
        combined_scores = {}
        
        # Semantic scores (1 - distance, assuming cosine distance)
        if semantic_results['distances']:
            for i, dist in enumerate(semantic_results['distances'][0]):
                chunk_id = semantic_results['ids'][0][i]
                combined_scores[chunk_id] = 0.7 * (1 - dist)
        
        # BM25 scores
        for i, score in enumerate(bm25_scores):
            chunk_id = list(self.chunk_data.keys())[i]  # Assuming order matches
            if chunk_id in combined_scores:
                combined_scores[chunk_id] += 0.3 * score
            else:
                combined_scores[chunk_id] = 0.3 * score
        
        # Sort by combined score
        sorted_items = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:n_results]
        
        # Format results
        formatted_results = []
        for chunk_id, score in sorted_items:
            data = self.chunk_data[chunk_id]
            formatted_results.append({
                'content': data['content'],
                'metadata': data['metadata'],
                'score': score
            })
        
        return formatted_results


def main():
    """Initialize and test the improved RAG system"""
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'rag-system'))
    from rag_evaluator import RAGEvaluator

    print("🚀 IMPROVED RAG SYSTEM TEST")
    print("Testing AWS Compliance Documentation Search")
    print("=" * 60)

    # Initialize system
    rag = ImprovedRAGSystem()

    # Process documents
    docs_path = "/root/rag-debugging/aws-compliance-docs"
    if not os.path.exists(docs_path):
        docs_path = os.path.join(os.path.dirname(__file__), "../aws-compliance-docs")

    if os.path.exists(docs_path):
        rag.process_documents(docs_path)
    else:
        print(f"❌ Documents not found at: {docs_path}")
        return

    # Initialize evaluator
    evaluator = RAGEvaluator(rag)

    # Run evaluation
    output_file = '/root/rag-debugging/improved_accuracy.txt'
    if not os.path.exists('/root'):
        output_file = './improved_accuracy.txt'

    results = evaluator.run_evaluation(output_file=output_file)


if __name__ == "__main__":
    main()