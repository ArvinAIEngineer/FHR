import pandas as pd
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict
import time

os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'

class LLMOutputEvaluator:
    def __init__(self, openai_api_key: str, openai_api_base:str="http://10.254.140.69:11434/v1", model_name: str = "qwen3:32b"):
        """
        Initialize the LLM Output Evaluator
        
        Args:
            openai_api_key (str): Your OpenAI API key
            model_name (str): OpenAI model to use for evaluation
        """
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model_name,
            temperature=0,  # Set to 0 for consistent evaluation results
            openai_api_base=openai_api_base
        )
    
    def evaluate_output(self, expected_output: str, ai_output: str) -> Dict[str, any]:
        """
        Evaluate if AI output is correct compared to expected output
        
        Args:
            expected_output (str): The expected/correct output
            ai_output (str): The AI-generated output to evaluate
            
        Returns:
            Dict containing evaluation results
        """
        system_prompt = """You are an expert evaluator tasked with determining if an AI output is correct compared to an expected output.

The AI output is considered CORRECT if it:
1. Totally contains the expected output (exact match or superset)
2. Partially contains the expected output (key information is present)

The AI output is considered INCORRECT if it:
1. Completely misses the expected content
2. Contains contradictory information
3. Is entirely unrelated to the expected output

Respond with ONLY a JSON object in this format:
{
    "is_correct": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your decision"
}"""

        human_prompt = f"""Expected Output: {expected_output}

AI Output: {ai_output}

Evaluate if the AI output is correct compared to the expected output."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm.invoke(messages)
            result_text = response.content.strip()

            # Remove <think> tags if present
            import re
            result_text = re.sub(r'<think>.*?</think>', '', result_text, flags=re.DOTALL).strip()


            # Try to parse JSON response
            import json
            try:
                result = json.loads(result_text)
                return {
                    'is_correct': result.get('is_correct', False),
                    'confidence': result.get('confidence', 0.0),
                    'reasoning': result.get('reasoning', 'No reasoning provided')
                }
            except json.JSONDecodeError:
                # Fallback: simple keyword detection
                is_correct = 'true' in result_text.lower() or 'correct' in result_text.lower()
                return {
                    'is_correct': is_correct,
                    'confidence': 0.5,
                    'reasoning': 'Parsed from text response'
                }
                
        except Exception as e:
            print(f"Error evaluating output: {str(e)}")
            return {
                'is_correct': False,
                'confidence': 0.0,
                'reasoning': f'Evaluation error: {str(e)}'
            }

    def process_excel_file(self, file_path: str, output_path: str = None) -> str:
        """
        Process Excel file and add evaluation results
        
        Args:
            file_path (str): Path to input Excel file
            output_path (str): Path for output file (optional)
            
        Returns:
            str: Path to the output file
        """
        try:
            # Read Excel file
            print(f"Reading Excel file: {file_path}")
            df = pd.read_excel(file_path)
            
            # Verify required columns exist
            required_columns = ['Expected Output', 'AI Output']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            print(f"Found {len(df)} rows to process")
            
            # Find the position of 'Passed' column
            if 'Passed' in df.columns:
                passed_index = df.columns.get_loc('Passed') + 1
            else:
                # If 'Passed' column doesn't exist, add at the end
                passed_index = len(df.columns)

            # Initialize new columns and insert them after 'Passed'
            df.insert(passed_index, 'LLM_Is_Correct', False)
            df.insert(passed_index + 1, 'LLM_Confidence', 0.0)
            df.insert(passed_index + 2, 'LLM_Reasoning', '')
            
            # Determine output path early
            if output_path is None:
                base_name = os.path.splitext(file_path)[0]
                output_path = f"{base_name}_evaluated.xlsx"

            # Process each row
            total_rows = len(df)
            for index, row in df.iterrows():
                print(f"Processing row {index + 1}/{total_rows}")
                
                expected = str(row['Expected Output']) if pd.notna(row['Expected Output']) else ''
                ai_output = str(row['AI Output']) if pd.notna(row['AI Output']) else ''
                
                # Skip empty rows
                if not expected.strip() or not ai_output.strip():
                    print(f"  Skipping row {index + 1}: Empty expected output or AI output")
                    continue
                
                # Evaluate the output
                evaluation = self.evaluate_output(expected, ai_output)
                
                # Update DataFrame
                df.at[index, 'LLM_Is_Correct'] = evaluation['is_correct']
                df.at[index, 'LLM_Confidence'] = evaluation['confidence']
                df.at[index, 'LLM_Reasoning'] = evaluation['reasoning']
                
                print(f"  Result: {'CORRECT' if evaluation['is_correct'] else 'INCORRECT'} (Confidence: {evaluation['confidence']:.2f})")
                
                # Save after each evaluation
                df.to_excel(output_path, index=False)
                print(f"  Saved progress to: {output_path}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            
            # Print summary
            df['LLM_Is_Correct'] = df['LLM_Is_Correct'].astype(bool)
            correct_count = int(df['LLM_Is_Correct'].sum())
            total_evaluated = int(df['LLM_Is_Correct'].count())
            accuracy = (correct_count / total_evaluated * 100) if total_evaluated > 0 else 0
            
            print(f"\nSummary:")
            print(f"  Total rows evaluated: {total_evaluated}")
            print(f"  Correct outputs: {correct_count}")
            print(f"  Incorrect outputs: {total_evaluated - correct_count}")
            print(f"  Accuracy: {accuracy:.1f}%")
            
            return output_path
            
        except Exception as e:
            print(f"Error processing Excel file: {str(e)}")
            raise

def main():
    """
    Main function to run the evaluation script
    """
    # Configuration
    OPENAI_API_KEY = "AI-key"   # Set this environment variable
    INPUT_FILE = './new/master_summary_20250811_Qwen_140.xlsx'  # Replace with your file path
    OUTPUT_FILE = None  # Will auto-generate if None
    
    # Validate API key
    if not OPENAI_API_KEY:
        print("Error: Please set the OPENAI_API_KEY environment variable")
        print("You can set it by running: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Validate input file
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found: {INPUT_FILE}")
        print("Please update the INPUT_FILE variable with the correct path to your Excel file")
        return
    
    try:
        # Initialize evaluator
        print("Initializing LLM Output Evaluator...")
        evaluator = LLMOutputEvaluator(
            openai_api_key=OPENAI_API_KEY,
        )
        
        # Process the Excel file
        output_path = evaluator.process_excel_file(INPUT_FILE, OUTPUT_FILE)
        print(f"\nEvaluation completed successfully!")
        print(f"Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Script failed with error: {str(e)}")

if __name__ == "__main__":
    main()