# -*- coding: utf-8 -*-
"""
VSTEP Exam Scraper - Main Script
Scrapes exam content and correct answers from luyenthivstep.vn
"""

import json
import os
import re
import time
import logging
import argparse
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Page, Browser

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables directly

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
BASE_URL = os.getenv("VSTEP_BASE_URL", "https://luyenthivstep.vn")
USERNAME = os.getenv("VSTEP_USERNAME", "")
PASSWORD = os.getenv("VSTEP_PASSWORD", "")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data")

# Validate required config
if not USERNAME or not PASSWORD:
    logger.warning("VSTEP_USERNAME and VSTEP_PASSWORD not set. Please create a .env file or set environment variables.")


class VstepScraper:
    """Main scraper class using Playwright"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    def start(self):
        """Start browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        logger.info("Browser started")
        
    def stop(self):
        """Stop browser"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser stopped")
        
    def login(self) -> bool:
        """Login to website"""
        try:
            self.page.goto(f"{BASE_URL}/dang-nhap")
            self.page.wait_for_load_state("networkidle")
            
            self.page.fill("#user_name", USERNAME)
            self.page.fill("#password", PASSWORD)
            self.page.click("button.btn-primary")
            self.page.wait_for_load_state("networkidle")
            
            if "/dang-nhap" not in self.page.url:
                logger.info("Login successful")
                return True
            else:
                logger.error("Login failed")
                return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def _check_valid_page(self, exam_type: str) -> bool:
        """Check if current page is valid exam page"""
        current_url = self.page.url
        content = self.page.content()
        
        # Check for wrong redirects
        if "/tai-khoan" in current_url or "/dang-nhap" in current_url:
            return False
        
        # Check for VIP content
        if "Đây là mã đề VIP" in content or "cần nâng cấp tài khoản" in content:
            return False
            
        return True
    
    def scrape_listening(self, exam_id: int) -> Optional[Dict]:
        """Scrape listening exam with answers"""
        exam_url = f"{BASE_URL}/luyen-de/lam-bai-nghe/{exam_id}"
        
        try:
            logger.info(f"Scraping listening #{exam_id}")
            self.page.goto(exam_url)
            self.page.wait_for_load_state("networkidle")
            
            if not self._check_valid_page("listening"):
                logger.warning(f"Skipping listening #{exam_id}: Invalid page")
                return None
            
            # Extract questions
            exam_data = self.page.evaluate("""
                () => {
                    const data = {
                        title: document.title,
                        audio_url: null,
                        questions: []
                    };
                    
                    const audio = document.querySelector('audio source, audio');
                    if (audio) data.audio_url = audio.src || audio.querySelector('source')?.src;
                    
                    document.querySelectorAll('.question-block').forEach((block, i) => {
                        const q = { number: i + 1, text: '', options: {} };
                        
                        block.querySelectorAll('.form-check, label').forEach(opt => {
                            const text = opt.innerText.trim();
                            const match = text.match(/^([A-D])[\\.\\)\\s:]\\s*(.+)/);
                            if (match) q.options[match[1]] = match[2].trim();
                        });
                        
                        if (Object.keys(q.options).length > 0) data.questions.push(q);
                    });
                    
                    return data;
                }
            """)
            
            if len(exam_data['questions']) == 0:
                logger.warning(f"Skipping listening #{exam_id}: No questions")
                return None
            
            # Submit to get answers
            self.page.evaluate("""
                () => {
                    document.querySelectorAll('.question-block').forEach(q => {
                        const radio = q.querySelector('input[type="radio"]');
                        if (radio) radio.click();
                    });
                    window.confirm = () => true;
                }
            """)
            time.sleep(0.3)
            
            submit_btn = self.page.query_selector(".btn-submit")
            if submit_btn:
                submit_btn.click()
                self.page.wait_for_load_state("networkidle")
                time.sleep(0.5)
            
            # Extract correct answers
            if "ket-qua" in self.page.url:
                answers = self.page.evaluate("""
                    () => {
                        const ans = {};
                        document.querySelectorAll('.question-block').forEach((block, i) => {
                            const success = block.querySelector('span.text-success');
                            if (success) {
                                const match = success.innerText.trim().match(/^([A-D])/);
                                if (match) ans[i + 1] = match[1];
                            }
                        });
                        return ans;
                    }
                """)
                
                for q in exam_data['questions']:
                    q['correct_answer'] = answers.get(q['number']) or answers.get(str(q['number']))
            
            return {
                "exam_type": "listening",
                "exam_id": str(exam_id),
                "title": exam_data['title'],
                "source_url": exam_url,
                "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "audio_url": exam_data['audio_url'],
                "questions": [{
                    "question_number": q['number'],
                    "options": q['options'],
                    "correct_answer": q.get('correct_answer')
                } for q in exam_data['questions']]
            }
            
        except Exception as e:
            logger.error(f"Error scraping listening #{exam_id}: {e}")
            return None
    
    def scrape_reading(self, exam_id: int) -> Optional[Dict]:
        """Scrape reading exam with answers"""
        exam_url = f"{BASE_URL}/luyen-de/lam-bai-doc/{exam_id}"
        
        try:
            logger.info(f"Scraping reading #{exam_id}")
            self.page.goto(exam_url)
            self.page.wait_for_load_state("networkidle")
            
            if not self._check_valid_page("reading"):
                logger.warning(f"Skipping reading #{exam_id}: Invalid page")
                return None
            
            # Extract passages and questions
            exam_data = self.page.evaluate("""
                () => {
                    const data = { title: document.title, passages: [] };
                    
                    document.querySelectorAll('.card, .passage').forEach((card, pi) => {
                        const passage = { number: pi + 1, content: '', questions: [] };
                        
                        const body = card.querySelector('.card-body');
                        if (body) passage.content = body.innerText.trim().substring(0, 3000);
                        
                        card.querySelectorAll('.question-block').forEach((block, qi) => {
                            const q = { number: passage.questions.length + 1, options: {} };
                            
                            block.querySelectorAll('.form-check, label').forEach(opt => {
                                const text = opt.innerText.trim();
                                const match = text.match(/^([A-D])[\\.\\)\\s:]\\s*(.+)/);
                                if (match) q.options[match[1]] = match[2].trim();
                            });
                            
                            if (Object.keys(q.options).length > 0) passage.questions.push(q);
                        });
                        
                        if (passage.questions.length > 0) data.passages.push(passage);
                    });
                    
                    return data;
                }
            """)
            
            total_questions = sum(len(p['questions']) for p in exam_data['passages'])
            if total_questions == 0:
                logger.warning(f"Skipping reading #{exam_id}: No questions")
                return None
            
            # Submit to get answers
            self.page.evaluate("""
                () => {
                    document.querySelectorAll('.question-block').forEach(q => {
                        const radio = q.querySelector('input[type="radio"]');
                        if (radio) radio.click();
                    });
                    window.confirm = () => true;
                }
            """)
            time.sleep(0.3)
            
            submit_btn = self.page.query_selector(".btn-submit")
            if submit_btn:
                submit_btn.click()
                self.page.wait_for_load_state("networkidle")
                time.sleep(0.5)
            
            # Extract correct answers
            answers = {}
            if "ket-qua" in self.page.url:
                answers = self.page.evaluate("""
                    () => {
                        const ans = {};
                        document.querySelectorAll('.question-block').forEach((block, i) => {
                            const success = block.querySelector('span.text-success');
                            if (success) {
                                const match = success.innerText.trim().match(/^([A-D])/);
                                if (match) ans[i + 1] = match[1];
                            }
                        });
                        return ans;
                    }
                """)
            
            # Format output
            q_counter = 0
            formatted_passages = []
            for p in exam_data['passages']:
                formatted_questions = []
                for q in p['questions']:
                    q_counter += 1
                    formatted_questions.append({
                        "question_number": q_counter,
                        "options": q['options'],
                        "correct_answer": answers.get(q_counter) or answers.get(str(q_counter))
                    })
                formatted_passages.append({
                    "passage_number": p['number'],
                    "content": p['content'],
                    "questions": formatted_questions
                })
            
            return {
                "exam_type": "reading",
                "exam_id": str(exam_id),
                "title": exam_data['title'],
                "source_url": exam_url,
                "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "passages": formatted_passages
            }
            
        except Exception as e:
            logger.error(f"Error scraping reading #{exam_id}: {e}")
            return None
    
    def scrape_writing(self, exam_id: int) -> Optional[Dict]:
        """Scrape writing exam"""
        exam_url = f"{BASE_URL}/luyen-de/lam-bai-viet/{exam_id}"
        
        try:
            logger.info(f"Scraping writing #{exam_id}")
            self.page.goto(exam_url)
            self.page.wait_for_load_state("networkidle")
            
            if not self._check_valid_page("writing"):
                logger.warning(f"Skipping writing #{exam_id}: Invalid page")
                return None
            
            exam_data = self.page.evaluate("""
                () => {
                    const data = { title: document.title, tasks: [] };
                    
                    document.querySelectorAll('.card').forEach((card, i) => {
                        const task = { task_number: i + 1, prompt: '', word_limit: null };
                        
                        const body = card.querySelector('.card-body');
                        if (body) {
                            task.prompt = body.innerText.trim();
                            const match = body.innerText.match(/(\\d+)\\s*(?:words|từ)/i);
                            if (match) task.word_limit = parseInt(match[1]);
                        }
                        
                        if (task.prompt) data.tasks.push(task);
                    });
                    
                    return data;
                }
            """)
            
            if len(exam_data['tasks']) == 0:
                logger.warning(f"Skipping writing #{exam_id}: No tasks")
                return None
            
            return {
                "exam_type": "writing",
                "exam_id": str(exam_id),
                "title": exam_data['title'],
                "source_url": exam_url,
                "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "tasks": exam_data['tasks']
            }
            
        except Exception as e:
            logger.error(f"Error scraping writing #{exam_id}: {e}")
            return None
    
    def scrape_speaking(self, exam_id: int) -> Optional[Dict]:
        """Scrape speaking exam"""
        exam_url = f"{BASE_URL}/luyen-de/lam-bai-noi/{exam_id}"
        
        try:
            logger.info(f"Scraping speaking #{exam_id}")
            self.page.goto(exam_url)
            self.page.wait_for_load_state("networkidle")
            
            if not self._check_valid_page("speaking"):
                logger.warning(f"Skipping speaking #{exam_id}: Invalid page")
                return None
            
            exam_data = self.page.evaluate("""
                () => {
                    const cleanPatterns = [
                        /🎤 Ghi âm câu trả lời:/g,
                        /⏱ Thời gian ghi âm.*/g,
                        /⏺ Bắt đầu ghi âm/g,
                        /⏹ Dừng ghi âm/g,
                        /📤 Nộp bài/g,
                        /⏱ --:--/g
                    ];
                    
                    function clean(text) {
                        if (!text) return '';
                        let t = text;
                        cleanPatterns.forEach(p => t = t.replace(p, ''));
                        return t.replace(/\\n{3,}/g, '\\n\\n').trim();
                    }
                    
                    const data = { title: document.title, parts: [] };
                    
                    document.querySelectorAll('.card').forEach((card, i) => {
                        const part = { 
                            part_number: i + 1, 
                            topic: '', 
                            instructions: '',
                            follow_up_questions: [],
                            speaking_time: null 
                        };
                        
                        const body = card.querySelector('.card-body');
                        if (body) {
                            part.instructions = clean(body.innerText);
                            
                            const topicMatch = body.innerText.match(/Topic:\\s*(.+?)(?:\\n|$)/i);
                            if (topicMatch) part.topic = topicMatch[1].trim();
                            
                            const timeMatch = body.innerText.match(/(\\d+)\\s*phút/i);
                            if (timeMatch) part.speaking_time = parseInt(timeMatch[1]);
                            
                            const followUp = body.innerText.match(/Follow-up questions?:([\\s\\S]*?)(?:Ghi âm|$)/i);
                            if (followUp) {
                                const qs = followUp[1].match(/\\d+\\.\\s+[^\\d]+/g);
                                if (qs) part.follow_up_questions = qs.map(q => q.trim());
                            }
                        }
                        
                        if (part.instructions.length > 20 || part.topic) {
                            data.parts.push(part);
                        }
                    });
                    
                    return data;
                }
            """)
            
            if len(exam_data['parts']) == 0:
                logger.warning(f"Skipping speaking #{exam_id}: No parts")
                return None
            
            return {
                "exam_type": "speaking",
                "exam_id": str(exam_id),
                "title": exam_data['title'],
                "source_url": exam_url,
                "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "parts": exam_data['parts']
            }
            
        except Exception as e:
            logger.error(f"Error scraping speaking #{exam_id}: {e}")
            return None
    
    def save(self, data: Dict, exam_type: str, exam_id: int):
        """Save exam data to JSON"""
        output_dir = os.path.join(OUTPUT_DIR, exam_type)
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f"{exam_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {filepath}")
    
    def scrape_all(self, exam_type: str, start_id: int, end_id: int):
        """Scrape all exams of a type"""
        scrape_func = {
            "listening": self.scrape_listening,
            "reading": self.scrape_reading,
            "writing": self.scrape_writing,
            "speaking": self.scrape_speaking
        }.get(exam_type)
        
        if not scrape_func:
            logger.error(f"Unknown exam type: {exam_type}")
            return
        
        success = 0
        for exam_id in range(start_id, end_id + 1):
            data = scrape_func(exam_id)
            if data:
                self.save(data, exam_type, exam_id)
                success += 1
            time.sleep(0.5)
        
        logger.info(f"Scraped {success}/{end_id - start_id + 1} {exam_type} exams")


def remove_duplicates(exam_type: str):
    """Remove duplicate exams based on content"""
    path = os.path.join(OUTPUT_DIR, exam_type)
    if not os.path.exists(path):
        return
    
    seen = {}
    removed = 0
    
    files = sorted(os.listdir(path), key=lambda x: int(x.replace('.json', '')))
    
    for f in files:
        filepath = os.path.join(path, f)
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Create content key based on exam type
        if exam_type == "listening":
            key = str(data.get('questions', [])[:3])
        elif exam_type == "reading":
            key = str([p.get('content', '')[:200] for p in data.get('passages', [])])
        elif exam_type == "writing":
            key = str([t.get('prompt', '')[:200] for t in data.get('tasks', [])])
        elif exam_type == "speaking":
            key = str([p.get('topic', '') + p.get('instructions', '')[:100] for p in data.get('parts', [])])
        else:
            key = json.dumps(data)
        
        if key in seen:
            os.remove(filepath)
            removed += 1
        else:
            seen[key] = f
    
    print(f"Removed {removed} duplicate {exam_type} exams")


def main():
    parser = argparse.ArgumentParser(description="VSTEP Exam Scraper")
    parser.add_argument("--type", choices=["listening", "reading", "writing", "speaking", "all"], 
                        required=True, help="Exam type to scrape")
    parser.add_argument("--start", type=int, default=1, help="Start exam ID")
    parser.add_argument("--end", type=int, default=100, help="End exam ID")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    parser.add_argument("--cleanup", action="store_true", help="Remove duplicate exams after scraping")
    
    args = parser.parse_args()
    
    scraper = VstepScraper(headless=not args.visible)
    
    try:
        scraper.start()
        
        if not scraper.login():
            logger.error("Login failed")
            return
        
        if args.type == "all":
            for t in ["listening", "reading", "writing", "speaking"]:
                scraper.scrape_all(t, args.start, args.end)
                if args.cleanup:
                    remove_duplicates(t)
        else:
            scraper.scrape_all(args.type, args.start, args.end)
            if args.cleanup:
                remove_duplicates(args.type)
        
    finally:
        scraper.stop()


if __name__ == "__main__":
    main()
