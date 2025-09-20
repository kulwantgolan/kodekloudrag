#!/usr/bin/env python3
"""
RAG System Evaluator
Separate module for testing and evaluating the RAG system performance
"""

import os
from typing import List, Dict

class RAGEvaluator:
    def __init__(self, rag_system):
        """Initialize evaluator with a RAG system instance"""
        self.rag = rag_system
        self.test_cases = self._define_test_cases()

    def _define_test_cases(self) -> List[Dict]:
        """Define all test cases for evaluation"""
        return [
            {
                "query": "What are the S3 encryption requirements?",
                "expected_terms": ["S3", "encryption", "AES-256", "KMS"],
                "must_have_all": ["S3", "encryption"]  # Must have BOTH terms
            },
            {
                "query": "What is policy AWS-POL-S3-001?",
                "expected_terms": ["AWS-POL-S3-001", "S3", "encryption"],
                "must_have_all": ["AWS-POL-S3-001"]  # Must have exact policy ID
            },
            {
                "query": "EC2 instance tagging requirements",
                "expected_terms": ["EC2", "tag", "Environment", "Owner"],
                "must_have_all": ["EC2", "tag"]  # Must have both
            },
            {
                "query": "CloudTrail logging configuration",
                "expected_terms": ["CloudTrail", "logging", "audit"],
                "must_have_all": ["CloudTrail", "logging"]  # Must have both
            },
            {
                "query": "VPC security group rules",
                "expected_terms": ["VPC", "security", "group", "rules"],
                "must_have_all": ["VPC", "security"]  # Must have both
            },
            {
                "query": "IAM password policy minimum length",
                "expected_terms": ["IAM", "password", "minimum", "length", "14"],
                "must_have_all": ["password", "14"]  # Must have specific value
            },
            {
                "query": "RDS encryption at rest requirements",
                "expected_terms": ["RDS", "encryption", "rest", "KMS"],
                "must_have_all": ["RDS", "encryption"]  # Must have both
            },
            {
                "query": "Lambda function timeout limits",
                "expected_terms": ["Lambda", "timeout", "900", "seconds"],
                "must_have_all": ["Lambda", "timeout"]  # Must have both
            },
            {
                "query": "EBS volume encryption policy",
                "expected_terms": ["EBS", "volume", "encryption", "required"],
                "must_have_all": ["EBS", "encryption"]  # Must have both
            },
            {
                "query": "CloudWatch log retention period",
                "expected_terms": ["CloudWatch", "log", "retention", "days"],
                "must_have_all": ["CloudWatch", "retention"]  # Must have both
            },
            {
                "query": "AWS-POL-EC2-002 compliance details",
                "expected_terms": ["AWS-POL-EC2-002", "EC2", "compliance"],
                "must_have_all": ["AWS-POL-EC2-002"]  # Must have exact policy
            }
        ]

    def test_accuracy(self, n_results: int = 2, verbose: bool = True) -> float:
        """
        Test the system accuracy

        Args:
            n_results: Number of results to retrieve per query
            verbose: Whether to print detailed results

        Returns:
            Accuracy percentage
        """
        correct = 0
        total = len(self.test_cases)

        if verbose:
            print("\n🧪 Testing RAG System with STRICT Criteria...")
            print("=" * 50)

        results_detail = []

        for test in self.test_cases:
            results = self.rag.search(test["query"], n_results=n_results)

            # STRICTER check: ALL required terms must be in the SAME result
            found = False
            for result in results:
                content = result['content'].lower()
                # Check if ALL must_have_all terms are in this single result
                if all(term.lower() in content for term in test["must_have_all"]):
                    found = True
                    break

            if found:
                correct += 1
                status = "✅"
            else:
                status = "❌"

            results_detail.append({
                "query": test["query"],
                "passed": found,
                "status": status
            })

            if verbose:
                print(f"{status} {test['query'][:40]}...")

        accuracy = (correct / total) * 100

        if verbose:
            print(f"\n📊 Accuracy: {accuracy:.1f}%")
            print(f"🎯 Target: 90%")
            print(f"📈 Gap: {90 - accuracy:.1f}%")

        return accuracy

    def run_evaluation(self, output_file: str = None) -> Dict:
        """
        Run full evaluation and save results

        Args:
            output_file: Optional file path to save results

        Returns:
            Dictionary with evaluation results
        """
        accuracy = self.test_accuracy()

        results = {
            "accuracy": accuracy,
            "target": 90,
            "gap": 90 - accuracy,
            "total_tests": len(self.test_cases),
            "passed": int(accuracy * len(self.test_cases) / 100)
        }

        # Save result if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"BASELINE:{accuracy}")
            print(f"\n📁 Results saved to: {output_file}")

        print(f"\n📊 System Performance:")
        print(f"Current Accuracy: {accuracy:.1f}%")
        print(f"Target Accuracy: 90%")
        if accuracy < 90:
            print(f"\n⚠️ System needs optimization to reach target accuracy")
            print("Consider analyzing the system for potential improvements.")

        return results

    def test_specific_query(self, query: str, n_results: int = 3) -> None:
        """
        Test a specific query and show detailed results

        Args:
            query: The query to test
            n_results: Number of results to retrieve
        """
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 50)

        results = self.rag.search(query, n_results=n_results)

        if not results:
            print("❌ No results found")
            return

        for i, result in enumerate(results, 1):
            print(f"\n📄 Result {i}:")
            print(f"   Source: {result.get('metadata', {}).get('source', 'Unknown')}")
            print(f"   Distance: {result.get('distance', 0):.4f}")
            print(f"   Content: {result['content'][:200]}...")