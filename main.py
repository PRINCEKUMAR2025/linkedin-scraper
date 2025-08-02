"""
LinkedIn Profile Analyzer - Main Application
Orchestrates the scraping and analysis process
"""

import os
import sys
import logging
import argparse
import csv
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file
from scraper import scrape_linkedin_profile
from summarizer import ProfileAnalyzer, analyze_profile
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, GEMINI_API_KEY

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_console_mode():
    """Run the application in console mode"""
    print("=" * 60)
    print("LinkedIn Profile Analyzer - Console Mode")
    print("=" * 60)
    
    # Check if Gemini API key is available
    if not GEMINI_API_KEY:
        print("❌ Error: Gemini API key not found!")
        print("Please set your GEMINI_API_KEY in the .env file or config.py")
        print("Get your API key from: https://aistudio.google.com/app/apikey")
        return
    
    print("✅ Gemini API key found")
    
    # Get LinkedIn profile URL
    profile_url = input("\nEnter LinkedIn profile URL: ").strip()
    
    if not profile_url:
        print("❌ No profile URL provided")
        return
    
    if "linkedin.com/in/" not in profile_url:
        print("\n❌ Invalid LinkedIn profile URL. Please provide a valid LinkedIn profile URL.\n")
        return
    
    print(f"\n🔍 Scraping profile: {profile_url}")
    print("\nNote: You will need to log in to LinkedIn manually when the browser opens.\n")
    
    # Scrape the profile
    try:
        profile_data = scrape_linkedin_profile(profile_url, headless=True)
        
        if not profile_data:
            print("\n\n\t\t❌ Failed to scrape profile data\n\n")
            return
        
        print("\n\n\t\t✅ Profile data scraped successfully!\n")
        print(f"Name: {profile_data.get('name', 'Unknown')}")
        print(f"Headline: {profile_data.get('headline', 'Unknown')}\n")
        print(f"About: {profile_data.get('about','Unknown')}\n")
        print(f"Skills: {profile_data.get('skills','Unknown')}\n")
        print(f"Experience: {profile_data.get('experience','Unknown')}\n")
        
        # Show available analysis modes
        print("\n📊 Available Analysis Modes:")
        print("1. Bio - Generate a professional LinkedIn bio")
        print("2. Tell me about this Profile - Create a networking summary for recruiters")
        print("3. Analysis - Comprehensive profile analysis with strengths/gaps")
        
        # Get user choice
        while True:
            choice = input("\nSelect analysis mode (1-3) or 'all' for all modes: ").strip().lower()
            
            if choice == '1':
                mode = 'bio'
                break
            elif choice == '2':
                mode = 'summary'
                break
            elif choice == '3':
                mode = 'analysis'
                break
            elif choice == 'all':
                mode = 'all'
                break
            else:
                print("❌ Invalid choice. Please select 1, 2, 3, or 'all'")
        
        # Generate analysis
        if mode == 'all':
            print("\n🤖 Generating all analysis types...")
            modes = ['bio', 'summary', 'analysis']
            
            for analysis_mode in modes:
                print(f"\n🔄 Generating {analysis_mode}...")
                result = analyze_profile(profile_data, analysis_mode)
                
                if not result or result.get('error'):
                    print(f"\n❌ Failed to generate {analysis_mode}")
                    continue
                
                print(f"\n{'=' * 60}")
                print(f"{analysis_mode.upper()}")
                print("=" * 60)
                print(result['result'])
                print("=" * 60)
        else:
            mode_names = {'bio': 'Bio', 'summary': 'Summary', 'analysis': 'Analysis'}
            print(f"\n🤖 Generating {mode_names[mode]}...")
            
            result = analyze_profile(profile_data, mode)
            
            if not result or result.get('error'):
                print(f"\n❌ Failed to generate {mode}")
                return
            
            print(f"\n{'=' * 60}")
            print(f"{mode_names[mode].upper()}")
            print("=" * 60)
            print(result['result'])
            print("=" * 60)
        
        # Ask if user wants to save the result
        save_result = input("\nWould you like to save the result to a file? (y/n): ").lower().strip()
        
        if save_result == 'y':
            try:
                analyzer = ProfileAnalyzer()
                if mode == 'all':
                    # Save all results
                    for analysis_mode in modes:
                        result = analyze_profile(profile_data, analysis_mode)
                        if result and not result.get('error'):
                            filename = analyzer.save_result(result)
                            if filename:
                                print(f"✅ {analysis_mode.capitalize()} saved to: {filename}")
                else:
                    filename = analyzer.save_result(result)
                    if filename:
                        print(f"✅ Result saved to: {filename}")
            except Exception as e:
                print(f"❌ Error saving file: {str(e)}")
        
        print("\n\n\t\t🎉 Process completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        logger.error(f"Error in console mode: {str(e)}")


def process_csv_batch(csv_file, url_column, analysis_mode):
    """Process a CSV file containing LinkedIn profile URLs using a single browser session"""
    results = []
    errors = []
    
    try:
        # Read CSV file
        csv_content = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(csv_content.splitlines())
        
        # Validate column exists
        if url_column not in csv_reader.fieldnames:
            raise ValueError(f"Column '{url_column}' not found in CSV. Available columns: {csv_reader.fieldnames}")
        
        # Get all URLs
        urls = []
        for row in csv_reader:
            url = row.get(url_column, '').strip()
            if url and "linkedin.com/in/" in url:
                urls.append(url)
        
        if not urls:
            raise ValueError("No valid LinkedIn URLs found in the CSV file")
        
        logger.info(f"Found {len(urls)} valid LinkedIn URLs to process")
        
        # Create a single scraper instance for all profiles
        from scraper import LinkedInScraper
        scraper = LinkedInScraper(headless=False)
        
        try:
            # Login once at the beginning
            logger.info("Logging in to LinkedIn...")
            if not scraper.login_to_linkedin():
                logger.error("Failed to login to LinkedIn. Please try again.")
                return [], [{'url': 'login_failed', 'error': 'Failed to login to LinkedIn', 'index': 0}]
            
            logger.info("✅ Successfully logged in to LinkedIn")
            
            # Process each URL using the same browser session
            for i, url in enumerate(urls, 1):
                try:
                    logger.info(f"Processing {i}/{len(urls)}: {url}")
                    
                    # Navigate to the profile using the same browser session
                    scraper.page.goto(url)
                    scraper.random_delay(2, 4)  # Wait for page to load
                    
                    # Scrape profile data using the existing session
                    profile_data = scraper.scrape_profile(url)
                    
                    if not profile_data:
                        error_msg = f"Failed to scrape profile: {url}"
                        logger.error(error_msg)
                        errors.append({
                            'url': url,
                            'error': error_msg,
                            'index': i
                        })
                        continue
                    
                    # Generate analysis
                    analysis_result = analyze_profile(profile_data, analysis_mode)
                    
                    if not analysis_result or analysis_result.get('error'):
                        error_msg = f"Failed to generate analysis for: {url}"
                        logger.error(error_msg)
                        errors.append({
                            'url': url,
                            'error': error_msg,
                            'index': i
                        })
                        continue
                    
                    # Store result
                    result = {
                        'url': url,
                        'profile_data': profile_data,
                        'analysis_result': analysis_result,
                        'index': i,
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(result)
                    
                    logger.info(f"✅ Successfully processed {i}/{len(urls)}: {profile_data.get('name', 'Unknown')}")
                    
                    # Add a small delay between profiles to be respectful
                    scraper.random_delay(3, 6)
                    
                except Exception as e:
                    error_msg = f"Error processing {url}: {str(e)}"
                    logger.error(error_msg)
                    errors.append({
                        'url': url,
                        'error': error_msg,
                        'index': i
                    })
            
        finally:
            # Close the browser session
            scraper.close()
        
        return results, errors
        
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise e


def save_batch_results(results, errors, analysis_mode):
    """Save batch processing results to CSV file with comprehensive data"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_results_{analysis_mode}_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'profile_url', 'name', 'headline', 'about', 
                'experience_raw', 'experience_formatted', 'experience_count',
                'skills_raw', 'skills_formatted', 'skills_count',
                'education_raw', 'education_formatted', 'education_count',
                'analysis_result', 'analysis_mode', 'timestamp', 'processing_index',
                'scraping_success', 'analysis_success'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                profile_data = result['profile_data']
                analysis_result = result['analysis_result']
                
                # Experience data
                experience_raw = profile_data.get('experience', [])
                experience_count = len(experience_raw)
                experience_formatted = '; '.join([
                    f"{exp.get('title', '')} at {exp.get('company', '')}"
                    for exp in experience_raw
                    if isinstance(exp, dict) and exp.get('title') and exp.get('company')
                ])
                
                # Skills data
                skills_raw = profile_data.get('skills', [])
                skills_count = len(skills_raw)
                skills_formatted = '; '.join(skills_raw) if skills_raw else ''
                
                # Education data
                education_raw = profile_data.get('education', [])
                education_count = len(education_raw)
                education_formatted = '; '.join(education_raw) if education_raw else ''
                
                # Convert raw data to JSON strings for CSV storage
                experience_raw_json = json.dumps(experience_raw, ensure_ascii=False)
                skills_raw_json = json.dumps(skills_raw, ensure_ascii=False)
                education_raw_json = json.dumps(education_raw, ensure_ascii=False)
                
                # Determine success flags
                scraping_success = 'Yes' if profile_data.get('name') else 'No'
                analysis_success = 'Yes' if analysis_result.get('result') else 'No'
                
                writer.writerow({
                    'profile_url': result['url'],
                    'name': profile_data.get('name', ''),
                    'headline': profile_data.get('headline', ''),
                    'about': profile_data.get('about', ''),
                    'experience_raw': experience_raw_json,
                    'experience_formatted': experience_formatted,
                    'experience_count': experience_count,
                    'skills_raw': skills_raw_json,
                    'skills_formatted': skills_formatted,
                    'skills_count': skills_count,
                    'education_raw': education_raw_json,
                    'education_formatted': education_formatted,
                    'education_count': education_count,
                    'analysis_result': analysis_result.get('result', ''),
                    'analysis_mode': analysis_mode,
                    'timestamp': result['timestamp'],
                    'processing_index': result['index'],
                    'scraping_success': scraping_success,
                    'analysis_success': analysis_success
                })
        
        # Save errors to separate file if any
        if errors:
            error_filename = f"batch_errors_{timestamp}.csv"
            with open(error_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['profile_url', 'error', 'index', 'timestamp', 'error_type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for error in errors:
                    # Determine error type
                    error_type = 'scraping_error' if 'Failed to scrape' in error['error'] else 'analysis_error'
                    
                    writer.writerow({
                        'profile_url': error['url'],
                        'error': error['error'],
                        'index': error['index'],
                        'timestamp': datetime.now().isoformat(),
                        'error_type': error_type
                    })
        
        # Create a summary report
        summary_filename = f"batch_summary_{timestamp}.txt"
        with open(summary_filename, 'w', encoding='utf-8') as summary_file:
            summary_file.write(f"LinkedIn Profile Analyzer - Batch Processing Summary\n")
            summary_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary_file.write(f"Analysis Mode: {analysis_mode}\n")
            summary_file.write(f"Total Profiles Processed: {len(results) + len(errors)}\n")
            summary_file.write(f"Successful Scrapes: {len(results)}\n")
            summary_file.write(f"Failed Scrapes: {len(errors)}\n")
            summary_file.write(f"Success Rate: {(len(results) / (len(results) + len(errors)) * 100):.1f}%\n\n")
            
            if results:
                summary_file.write("Successfully Processed Profiles:\n")
                for result in results:
                    profile_data = result['profile_data']
                    summary_file.write(f"- {profile_data.get('name', 'Unknown')} ({result['url']})\n")
            
            if errors:
                summary_file.write("\nFailed Profiles:\n")
                for error in errors:
                    summary_file.write(f"- {error['url']}: {error['error']}\n")
        
        return filename, error_filename if errors else None, summary_filename
        
    except Exception as e:
        logger.error(f"Error saving batch results: {str(e)}")
        raise e


def create_flask_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    
    @app.route('/')
    def index():
        """Main page"""
        return render_template('index.html')
    
    @app.route('/analyze', methods=['POST'])
    def analyze():
        """Handle profile analysis request"""
        try:
            profile_url = request.form.get('profile_url', '').strip()
            analysis_mode = request.form.get('analysis_mode', 'bio')
            
            use_sample = 'use_sample' in request.form
            
            if not use_sample:
                if not profile_url:
                    flash('Please provide a LinkedIn profile URL', 'error')
                    return redirect(url_for('index'))
                if "linkedin.com/in/" not in profile_url:
                    flash('Please provide a valid LinkedIn profile URL', 'error')
                    return redirect(url_for('index'))
            
            if not GEMINI_API_KEY:
                flash('Gemini API key not configured. Please check your configuration.', 'error')
                return redirect(url_for('index'))
            
            # Check if user wants to use sample data (for testing without scraping)
            if use_sample:
                # Use sample data for testing
                profile_data = {
                    'name': 'John Doe',
                    'headline': 'Senior Software Engineer at Tech Company',
                    'about': 'Passionate software engineer with 5+ years of experience in full-stack development, specializing in Python, JavaScript, and cloud technologies. I love building scalable applications and mentoring junior developers.',
                    'experience': [
                        {'title': 'Senior Software Engineer', 'company': 'Tech Corp'},
                        {'title': 'Software Engineer', 'company': 'Startup Inc'},
                        {'title': 'Junior Developer', 'company': 'Web Solutions'}
                    ],
                    'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'Git', 'SQL', 'MongoDB', 'REST APIs'],
                    'url': profile_url
                }
                flash('Using sample data for demonstration', 'info')
            else:
                # Scrape the actual profile - use headless=False for web mode so users can see the browser
                profile_data = scrape_linkedin_profile(profile_url, headless=False)
                
                if not profile_data:
                    flash('Failed to scrape profile data. Please check the URL and try again.', 'error')
                    return redirect(url_for('index'))
            
            # Generate analysis
            analysis_result = analyze_profile(profile_data, analysis_mode)
            
            if not analysis_result or analysis_result.get('error'):
                flash('Failed to generate analysis. Please check your Gemini API key.', 'error')
                return redirect(url_for('index'))
            
            return render_template('result.html', 
                                profile_data=profile_data, 
                                analysis_result=analysis_result)
            
        except Exception as e:
            logger.error(f"Error in Flask route: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/batch_analyze', methods=['POST'])
    def batch_analyze():
        """Handle batch analysis request"""
        try:
            if 'csv_file' not in request.files:
                flash('No CSV file uploaded', 'error')
                return redirect(url_for('index'))
            
            csv_file = request.files['csv_file']
            if csv_file.filename == '':
                flash('No CSV file selected', 'error')
                return redirect(url_for('index'))
            
            if not csv_file.filename.endswith('.csv'):
                flash('Please upload a CSV file', 'error')
                return redirect(url_for('index'))
            
            url_column = request.form.get('url_column', 'profile_url').strip()
            analysis_mode = request.form.get('analysis_mode', 'bio')
            
            if not GEMINI_API_KEY:
                flash('Gemini API key not configured. Please check your configuration.', 'error')
                return redirect(url_for('index'))
            
            # Process the CSV file
            results, errors = process_csv_batch(csv_file, url_column, analysis_mode)
            
            if not results and not errors:
                flash('No valid LinkedIn URLs found in the CSV file', 'error')
                return redirect(url_for('index'))
            
            # Save results to CSV
            try:
                results_filename, errors_filename, summary_filename = save_batch_results(results, errors, analysis_mode)
                
                # Create summary message
                success_count = len(results)
                error_count = len(errors)
                total_count = success_count + error_count
                
                summary_message = f"Batch processing completed! Processed {total_count} profiles: {success_count} successful, {error_count} failed."
                
                if results_filename:
                    summary_message += f" Results saved to: {results_filename}"
                if errors_filename:
                    summary_message += f" Errors saved to: {errors_filename}"
                if summary_filename:
                    summary_message += f" Summary saved to: {summary_filename}"
                
                flash(summary_message, 'info')
                
                # Return the results file for download
                return send_file(
                    results_filename,
                    as_attachment=True,
                    download_name=results_filename,
                    mimetype='text/csv'
                )
                
            except Exception as e:
                logger.error(f"Error saving batch results: {str(e)}")
                flash(f'Error saving results: {str(e)}', 'error')
                return redirect(url_for('index'))
            
        except Exception as e:
            logger.error(f"Error in batch analysis route: {str(e)}")
            flash(f'An error occurred during batch processing: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/api/analyze', methods=['POST'])
    def api_analyze():
        """API endpoint for profile analysis"""
        try:
            data = request.get_json()
            profile_url = data.get('profile_url', '').strip()
            analysis_mode = data.get('analysis_mode', 'bio')
            
            if not profile_url:
                return jsonify({'error': 'Profile URL is required'}), 400
            
            if not GEMINI_API_KEY:
                return jsonify({'error': 'Gemini API key not configured'}), 500
            
            # Scrape profile
            profile_data = scrape_linkedin_profile(profile_url, headless=False)
            
            if not profile_data:
                return jsonify({'error': 'Failed to scrape profile data'}), 400
            
            # Generate analysis
            analysis_result = analyze_profile(profile_data, analysis_mode)
            
            if not analysis_result or analysis_result.get('error'):
                return jsonify({'error': 'Failed to generate analysis'}), 500
            
            return jsonify({
                'success': True,
                'profile_data': profile_data,
                'analysis': analysis_result
            })
            
        except Exception as e:
            logger.error(f"Error in API route: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return app


def run_flask_mode():
    """Run the application in Flask web mode"""
    print("=" * 60)
    print("LinkedIn Profile Analyzer - Web Mode")
    print("=" * 60)
    
    if not GEMINI_API_KEY:
        print("❌ Error: Gemini API key not found!")
        print("Please set your GEMINI_API_KEY in the .env file or config.py")
        return
    
    print("✅ Gemini API key found")
    print(f"🌐 Starting web server at http://{FLASK_HOST}:{FLASK_PORT}")
    print("Press Ctrl+C to stop the server")
    
    app = create_flask_app()
    
    try:
        app.run(
            host=FLASK_HOST,
            port=FLASK_PORT,
            debug=FLASK_DEBUG
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Profile Analyzer")
    parser.add_argument("--mode", choices=["console", "web"], default="web",
                        help="Run in console or web mode")
    args = parser.parse_args()

    if args.mode == "console":
        run_console_mode()
    else:
        run_flask_mode()


if __name__ == "__main__":
    main()