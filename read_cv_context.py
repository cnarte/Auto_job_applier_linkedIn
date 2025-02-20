import fitz  # PyMuPDF
from config.questions import (
    years_of_experience, require_visa, website, linkedIn, us_citizenship,
    desired_salary, current_ctc, notice_period, linkedin_headline,
    linkedin_summary, cover_letter, recent_employer, confidence_level,
    first_name, last_name, location
)

def process_pdf(file_path):
        """Extract content and structure as YAML for LLM processing."""
        content_sections = {
            'contact_info': [],
            'education': [],
            'experience': [],
            'skills': [],
            'projects': [],
            'other': [],
            'personal_info': {
                'first_name': first_name,
                'last_name': last_name,
                'location': location,
                'years_of_experience': years_of_experience,
                'require_visa': require_visa,
                'website': website,
                'linkedin': linkedIn,
                'citizenship': us_citizenship,
                'desired_salary': str(desired_salary),
                'current_ctc': str(current_ctc),
                'notice_period': str(notice_period),
                'linkedin_headline': linkedin_headline,
                'linkedin_summary': linkedin_summary,
                'cover_letter': cover_letter,
                'recent_employer': recent_employer,
                'confidence_level': confidence_level
            }
        }
        
        try:
            pdf_document = fitz.open(file_path)
            current_section = 'other'
            
            for page in pdf_document:
                page_text = page.get_text()
                
                # Process text into sections based on common CV headers
                lines = page_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Detect section headers
                    lower_line = line.lower()
                    if any(header in lower_line for header in ['education', 'academic']):
                        current_section = 'education'
                        continue
                    elif any(header in lower_line for header in ['experience', 'employment', 'work history']):
                        current_section = 'experience'
                        continue
                    elif any(header in lower_line for header in ['skills', 'technologies', 'competencies']):
                        current_section = 'skills'
                        continue
                    elif any(header in lower_line for header in ['projects', 'portfolio']):
                        current_section = 'projects'
                        continue
                    elif any(header in lower_line for header in ['contact', 'email', 'phone', 'address']):
                        current_section = 'contact_info'
                        continue
                    
                    # Add line to current section
                    content_sections[current_section].append(line)
            
            pdf_document.close()
            
            # Convert to YAML-formatted string
            yaml_content = "cv_content:\n"
            for section, content in content_sections.items():
                if content:
                    yaml_content += f"  {section}:\n"
                    if isinstance(content, dict):
                        for key, value in content.items():
                            yaml_content += f"    {key}: {value}\n"
                    else:
                        for item in content:
                            yaml_content += f"    - {item}\n"
            
            return yaml_content
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        
        
if __name__ == "__main__":
    # Path to test file
    test_file = r"C:/Users/NIGHTWOLF/ankit_project/Auto_job_applier_linkedIn shanu/all resumes/Kalyani_Resume.pdf"
    
    # Read and parse the PDF
    yaml_content  = process_pdf(test_file)
    
    # Print the extracted content
    print("Extracted CV Content:")
    print("-" * 50)
    print(yaml_content)
    


