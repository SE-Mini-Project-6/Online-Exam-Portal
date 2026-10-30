"""Chrome/Firefox compatibility checks for NFR-07 and the scripted task flow behind NFR-03.

Seeds throwaway data, starts the dev server, drives each installed browser through the
student and admin flows at desktop and phone widths, then removes the data.

    pip install selenium
    python Deliverable-4-Test-Validation/browser_checks/run_browser_checks.py

Writes results.json and screenshots to Deliverable-4-Test-Validation/browser_checks/evidence/.
Selenium Manager downloads the matching chromedriver/geckodriver on first run.
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'Online_Exam_Portal'
EVIDENCE = Path(__file__).resolve().parent / 'evidence'
PORT = 8791
BASE = f'http://127.0.0.1:{PORT}'
TAG = uuid.uuid4().hex[:6]
PASSWORD = 'Pw-' + uuid.uuid4().hex
VIEWPORTS = {'desktop': (1280, 800), 'phone': (375, 812)}
ENV = {**os.environ, 'DJANGO_DEBUG': 'True', 'PYTHONUTF8': '1'}

SEED = f"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from exams.models import Exam, Question
U = get_user_model()
U.objects.create_user('bc-student-{TAG}', password='{PASSWORD}')
U.objects.create_user('bc-admin-{TAG}', password='{PASSWORD}', is_staff=True)
now = timezone.now()
exam = Exam.objects.create(title='Browser check {TAG}', duration_minutes=30,
                           start_at=now - timedelta(minutes=5), end_at=now + timedelta(hours=2))
for i in range(1, 4):
    Question.objects.create(exam=exam, text=f'Question {{i}}: which option is correct?', option_a='Alpha',
                            option_b='Beta', option_c='Gamma', option_d='Delta', correct_option='A')
print(exam.id)
"""
CLEANUP = f"""
from django.contrib.auth import get_user_model
from exams.models import Exam
Exam.objects.filter(title='Browser check {TAG}').delete()
get_user_model().objects.filter(username__in=['bc-student-{TAG}', 'bc-admin-{TAG}']).delete()
"""


def manage(*args):
    return subprocess.run([sys.executable, 'manage.py', *args], cwd=PROJECT, env=ENV,
                          capture_output=True, text=True, check=True).stdout


def make_driver(name):
    if name == 'chrome':
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        return webdriver.Chrome(options=options)
    options = webdriver.FirefoxOptions()
    options.add_argument('-headless')
    return webdriver.Firefox(options=options)


class Run:
    def __init__(self, browser, viewport):
        self.browser, self.viewport = browser, viewport
        self.results = []
        self.driver = make_driver(browser)
        self.driver.set_window_size(*VIEWPORTS[viewport])
        self.shots = EVIDENCE / browser
        self.shots.mkdir(parents=True, exist_ok=True)

    def check(self, name, ok, detail=''):
        self.results.append({'check': name, 'ok': bool(ok), 'detail': str(detail)})

    def fits(self, label):
        """No horizontal scrolling: the page must fit the viewport width."""
        d = self.driver
        width, inner = d.execute_script('return [document.documentElement.scrollWidth, window.innerWidth]')
        self.check(f'{label}: fits {self.viewport} width (no horizontal scroll)', width <= inner + 1,
                   f'scrollWidth={width} innerWidth={inner}')
        d.save_screenshot(str(self.shots / f'{self.viewport}-{label.replace(" ", "_")}.png'))

    def wait(self, condition, timeout=10):
        return WebDriverWait(self.driver, timeout).until(condition)

    def login(self, path, user):
        d = self.driver
        d.get(BASE + path)
        d.find_element(By.ID, 'username').send_keys(user)
        d.find_element(By.ID, 'password').send_keys(PASSWORD)
        d.find_element(By.CSS_SELECTOR, 'form button[type=submit]').click()
        self.wait(lambda dr: 'dashboard' in dr.current_url)

    def logout(self):
        self.driver.find_element(By.ID, 'logout-button').click()
        self.wait(lambda dr: 'dashboard' not in dr.current_url)

    def student_flow(self, exam_id):
        d = self.driver
        d.get(BASE + '/accounts/student-login/')
        self.check('login page renders form', d.find_element(By.ID, 'username').is_displayed())
        self.fits('student login')
        self.login('/accounts/student-login/', f'bc-student-{TAG}')
        self.check('student dashboard shows username', f'bc-student-{TAG}' in d.find_element(By.ID, 'nav-username').text)
        self.check('student dashboard lists the exam', d.find_element(By.ID, f'exam-row-{exam_id}').is_displayed())
        self.fits('student dashboard')

        d.get(BASE + '/exams/available/')
        self.fits('available exams')

        d.get(f'{BASE}/exams/{exam_id}/take/')
        self.check('question page shows question 1 of 3', 'Question 1 of 3' in d.find_element(By.ID, 'question-progress').text)
        self.check('countdown timer renders',
                   'Time remaining' in d.find_element(By.ID, 'exam-countdown').text)
        self.fits('question page')

        # NFR-03 tasks: answer, mark for review, move on, submit.
        d.find_element(By.CSS_SELECTOR, 'input[name=answer][value=B]').click()
        started = time.time()
        self.wait(lambda dr: 'Saved' in dr.find_element(By.ID, 'save-status').text, 2)
        self.check('answer click autosaves within 2 s', True, f'{(time.time() - started) * 1000:.0f} ms incl. polling')
        d.find_element(By.CSS_SELECTOR, 'input[name=mark_for_review]').click()
        self.wait(lambda dr: dr.find_element(By.CSS_SELECTOR, '#question-grid button[data-number="1"]')
                  .get_attribute('data-state') == 'ANSWERED_MARKED_FOR_REVIEW', 5)
        self.check('grid shows answered + marked for review', True)

        d.get(f'{BASE}/exams/{exam_id}/take/?question=1')  # refresh keeps the saved answer (NFR-02)
        self.check('refresh keeps saved answer', d.find_element(By.CSS_SELECTOR, 'input[name=answer][value=B]').is_selected())
        d.find_elements(By.CSS_SELECTOR, '.q-nav button')[1].click()  # Next
        self.wait(lambda dr: 'Question 2 of 3' in dr.find_element(By.ID, 'question-progress').text)
        self.check('Next moves to question 2', True)

        d.find_element(By.CSS_SELECTOR, 'button[value=review_submission]').click()
        self.wait(lambda dr: 'Confirm exam submission' in dr.find_element(By.TAG_NAME, 'h1').text)
        self.check('confirmation shows 1 of 3 answered', '1 of 3' in d.find_element(By.CSS_SELECTOR, '.panel').text)
        self.fits('confirm submission')
        d.find_element(By.CSS_SELECTOR, '.panel form button[type=submit]').click()
        self.wait(lambda dr: 'submitted successfully' in dr.find_element(By.TAG_NAME, 'h1').text)
        self.check('submission reaches submitted page', True)
        self.fits('submitted')
        self.logout()

    def admin_flow(self, exam_id):
        d = self.driver
        self.login('/accounts/login/', f'bc-admin-{TAG}')
        self.check('admin dashboard shows username', f'bc-admin-{TAG}' in d.find_element(By.ID, 'nav-username').text)
        self.fits('admin dashboard')
        d.get(BASE + '/exams/create/')
        self.check('create exam form renders', len(d.find_elements(By.CSS_SELECTOR, 'form input')) > 3)
        self.fits('create exam')
        d.get(f'{BASE}/exams/{exam_id}/questions/')
        self.check('question list renders 3 questions', d.page_source.count('which option is correct?') >= 3)
        self.fits('question list')
        d.get(f'{BASE}/exams/{exam_id}/questions/add/')
        self.fits('add question')

    def finish(self):
        info = self.driver.capabilities
        console = []
        if self.browser == 'chrome':
            console = [e for e in self.driver.get_log('browser') if e['level'] == 'SEVERE']
        self.check('no severe browser console errors' if console == [] and self.browser == 'chrome'
                   else 'console log check', not console,
                   'not available in Firefox/geckodriver' if self.browser != 'chrome' else console)
        version = info.get('browserVersion')
        self.driver.quit()
        return version


def main():
    EVIDENCE.mkdir(exist_ok=True)
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', PORT)) == 0:
            sys.exit(f'Port {PORT} is already in use; stop that server or change PORT, '
                     'otherwise the checks would hit a different instance.')
    manage('migrate', '-v0')
    exam_id = int(manage('shell', '-c', SEED).strip().splitlines()[-1])
    server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{PORT}', '--noreload'],
                              cwd=PROJECT, env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report = []
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(BASE + '/', timeout=1)
                break
            except Exception:
                time.sleep(0.3)
        for browser in ('chrome', 'firefox'):
            for viewport in VIEWPORTS:
                # The student flow consumes the attempt, so each run gets a fresh student attempt.
                manage('shell', '-c', f'from exams.models import Attempt; Attempt.objects.filter(exam_id={exam_id}).delete()')
                run = Run(browser, viewport)
                try:
                    run.student_flow(exam_id)
                    run.admin_flow(exam_id)
                except Exception as exc:  # a crash is a failed check, not a skipped one
                    run.check('flow completed without exception', False, f'{type(exc).__name__} at line {exc.__traceback__.tb_next.tb_lineno if exc.__traceback__.tb_next else "?"} '
                              f'(after: {run.results[-1]["check"] if run.results else "start"}): {str(exc).strip()[:150]}')
                    run.driver.save_screenshot(str(run.shots / f'{viewport}-FAILURE.png'))
                version = run.finish()
                report.append({'browser': browser, 'version': version, 'viewport': viewport, 'results': run.results})
                passed = sum(r['ok'] for r in run.results)
                print(f'{browser} {version} {viewport}: {passed}/{len(run.results)} checks passed')
                for r in run.results:
                    if not r['ok']:
                        print(f'   FAIL {r["check"]} {r["detail"]}')
    finally:
        server.terminate()
        manage('shell', '-c', CLEANUP)
    (EVIDENCE / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    sys.exit(0 if all(r['ok'] for run in report for r in run['results']) else 1)


if __name__ == '__main__':
    main()
