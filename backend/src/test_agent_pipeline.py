from src.agents.product_analyzer import ProductAnalyzerAgent, ProductAnalyzerInput
import os
from dotenv import load_dotenv
load_dotenv()

def main():
    # Example input (adjust as needed)
    input_data = ProductAnalyzerInput(
        job_id="test-job-001",
        user_id="test-user-001",
        title="Test Product",
        description="A sample product for testing.",
        price="19.99",
        image_keys=["dummy-image-key"]  # Add S3 image keys if you want to test vision
    )

    agent = ProductAnalyzerAgent()
    output = agent.run(input_data)
    print("Agent Output:", output)

if __name__ == "__main__":
    main()