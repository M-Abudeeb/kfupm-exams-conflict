import os
from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

# API endpoint and term code for exam schedule
API_URL = "https://registrar.kfupm.edu.sa/api/final-examination-schedule"
TERM_CODE = '202330'  # Update the term code as necessary

def fetch_exam_data():
    params = {'term_code': TERM_CODE}
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        data = response.json().get('data', [])
        return data
    return []

def extract_term_display(term_code):
    """Convert the six-digit term code into a '233' format."""
    year_last_digit = term_code[2]  # Get the last digit of the year (2023 -> 3)
    semester_code = term_code[4]    # Get the semester part ('3' for the third semester)
    return f"{year_last_digit}{semester_code}{semester_code}"  # Return '233' for '202330'


def detect_conflicts(courses, exam_data):
    conflicts = []
    exam_times = []
    for exam in exam_data:
        if exam['course_number'] in courses:
            exam_datetime = datetime.strptime(f"{exam['date']} {exam['time']}", "%d-%b-%y %I:%M %p")
            exam_info = {
                'course': exam['course_number'],
                'title': exam['course_title'],
                'datetime': exam_datetime,
                'location': exam.get('location', 'N/A'),
                'day': exam_datetime.strftime('%A')  # Get the day of the week
            }
            exam_times.append(exam_info)

    # Check for conflicts (by date only)
    for i in range(len(exam_times)):
        for j in range(i + 1, len(exam_times)):
            if exam_times[i]['datetime'].date() == exam_times[j]['datetime'].date():
                conflict = (exam_times[i]['course'], exam_times[j]['course'])
                conflicts.append(conflict)

    return conflicts

@app.route('/')
def index():
    # Fetch the course list from the API
    exam_data = fetch_exam_data()  # Fetch exam schedule data
    
    # Extract unique course numbers
    course_list = sorted({exam['course_number'] for exam in exam_data})
    
    # Calculate term to display (in the format of '233')
    term_display = extract_term_display(TERM_CODE)
    
    # Pass the course list to the template
    return render_template('index.html', courses=course_list, term=term_display)


@app.route('/check_conflicts', methods=['POST'])
def check_conflicts():
    # Get the selected courses from the form
    selected_courses = request.form.getlist('courses')  # Get the list of selected courses
    
    # Fetch exam schedule data
    exam_data = fetch_exam_data()  # This function fetches the full schedule
    
    # Filter out only the selected courses from the fetched data
    schedule_details = [exam for exam in exam_data if exam['course_number'] in selected_courses]
    
    # Detect conflicts in the selected courses
    conflicts = detect_conflicts(selected_courses, exam_data)  # Detect conflicts among selected courses
    
    # Calculate term to display (in the format of '233')
    term_display = extract_term_display(TERM_CODE)
    
    # Render the results.html template and pass both conflicts and schedule
    return render_template('results.html', conflicts=conflicts, schedule=schedule_details, term=term_display)



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
