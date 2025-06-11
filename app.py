from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
import os
import json
from uuid import uuid4
from datetime import datetime
import random
import csv
import io

app = Flask(__name__)

DATA_DIR = 'data'
HABITS_FILE = os.path.join(DATA_DIR, 'habits.json')

# Ensure data directory and habits.json exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(HABITS_FILE):
    with open(HABITS_FILE, 'w') as f:
        json.dump({'habits': []}, f)

def load_habits():
    with open(HABITS_FILE, 'r') as f:
        return json.load(f)

def save_habits(data):
    with open(HABITS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_unlogged_habits_today(habits):
    today = datetime.now().strftime('%Y-%m-%d')
    unlogged = []
    for h in habits:
        if today not in (h.get('logs', []) + h.get('failures', [])) and not h.get('archived', False):
            unlogged.append(h)
    return unlogged

def get_all_tags(habits):
    tags = set()
    for h in habits:
        for t in h.get('tags', []):
            tags.add(t)
    return sorted(tags)

@app.route('/')
def dashboard():
    data = load_habits()
    quote = get_random_quote()
    dark_mode = request.cookies.get('dark_mode', '0') == '1'
    unlogged = get_unlogged_habits_today(data['habits'])
    tags = get_all_tags(data['habits'])
    from datetime import datetime
    now = datetime.now()
    current_week = int(now.strftime('%W'))
    current_year = int(now.strftime('%Y'))
    return render_template('dashboard.html', habits=data['habits'], quote=quote, dark_mode=dark_mode, unlogged=unlogged, tags=tags, current_week=current_week, current_year=current_year)

@app.route('/add', methods=['GET', 'POST'])
def add_habit():
    if request.method == 'POST':
        name = request.form['name']
        habit_type = request.form['type']
        target = request.form['target']
        start_date = request.form['start_date']
        notes = request.form.get('notes', '')
        new_habit = {
            'id': str(uuid4()),
            'name': name,
            'type': habit_type,
            'target': target,
            'start_date': start_date,
            'logs': [],
            'journal': {},
            'milestones': [],
            'notes': notes,
            'failures': [],
            'archived': False,
            'tags': [],
            'custom_milestones': []
        }
        data = load_habits()
        data['habits'].append(new_habit)
        save_habits(data)
        return redirect(url_for('dashboard'))
    return render_template('add_habit.html')

@app.route('/log/<habit_id>/<status>', methods=['POST'])
def log_habit(habit_id, status):
    data = load_habits()
    today = datetime.now().strftime('%Y-%m-%d')
    milestone_celebration = None
    for habit in data['habits']:
        if habit['id'] == habit_id:
            if status == 'done':
                if today not in habit['logs']:
                    habit['logs'].append(today)
            elif status == 'fail':
                if 'failures' not in habit:
                    habit['failures'] = []
                if today not in habit['failures']:
                    habit['failures'].append(today)
            # Milestone detection
            streaks = detect_milestones(habit.get('logs', []), habit.get('custom_milestones'))
            last_celebrated = habit.get('last_celebrated_milestone')
            if streaks:
                new_milestone = streaks[-1]
                if new_milestone != last_celebrated:
                    habit['last_celebrated_milestone'] = new_milestone
                    milestone_celebration = new_milestone
            break
    save_habits(data)
    ref = request.referrer or url_for('dashboard')
    # Pass milestone celebration via query param if needed
    if milestone_celebration:
        return redirect(f"{ref}?milestone={milestone_celebration}")
    return redirect(ref)

@app.route('/delete/<habit_id>', methods=['POST'])
def delete_habit(habit_id):
    data = load_habits()
    data['habits'] = [h for h in data['habits'] if h['id'] != habit_id]
    save_habits(data)
    return redirect(url_for('dashboard'))

@app.route('/progression_data')
def progression_data():
    data = load_habits()
    return jsonify(data['habits'])

@app.route('/filter')
def filter_habits():
    filter_type = request.args.get('type')
    filter_tag = request.args.get('tag')
    data = load_habits()
    filtered = data['habits']
    if filter_type:
        filtered = [h for h in filtered if h['type'] == filter_type]
    if filter_tag:
        filtered = [h for h in filtered if filter_tag in h.get('tags', [])]
    tags = get_all_tags(data['habits'])
    return render_template('dashboard.html', habits=filtered, quote=get_random_quote(), dark_mode=request.cookies.get('dark_mode', '0') == '1', unlogged=get_unlogged_habits_today(filtered), tags=tags)

@app.route('/habit/<habit_id>')
def habit_detail(habit_id):
    data = load_habits()
    habit = next((h for h in data['habits'] if h['id'] == habit_id), None)
    if not habit:
        return redirect(url_for('dashboard'))
    weekly = get_weekly_summary(habit.get('logs', []))
    monthly = get_monthly_summary(habit.get('logs', []))
    milestones = detect_milestones(habit.get('logs', []), habit.get('custom_milestones'))
    dark_mode = request.cookies.get('dark_mode', '0') == '1'
    return render_template('habit_detail.html', habit=habit, weekly=weekly, monthly=monthly, milestones=milestones, dark_mode=dark_mode)

@app.route('/habit_progression/<habit_id>')
def habit_progression(habit_id):
    data = load_habits()
    habit = next((h for h in data['habits'] if h['id'] == habit_id), None)
    if not habit:
        return jsonify({})
    # Return logs and failures for charting
    return jsonify({
        'logs': habit.get('logs', []),
        'failures': habit.get('failures', []),
        'start_date': habit.get('start_date', '')
    })

@app.route('/habit/<habit_id>/journal', methods=['POST'])
def add_journal_entry(habit_id):
    data = load_habits()
    today = datetime.now().strftime('%Y-%m-%d')
    entry = request.form.get('journal_entry', '').strip()
    for habit in data['habits']:
        if habit['id'] == habit_id:
            if 'journal' not in habit:
                habit['journal'] = {}
            habit['journal'][today] = entry
            break
    save_habits(data)
    return redirect(url_for('habit_detail', habit_id=habit_id))

def get_random_quote():
    try:
        with open('data/quotes.json') as f:
            quotes = json.load(f)
        return random.choice(quotes)
    except Exception:
        return "Excellence is not an act, but a habit. – Aristotle"

def get_weekly_summary(logs):
    from collections import defaultdict
    import datetime
    summary = defaultdict(int)
    for date_str in logs:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        year, week, _ = dt.isocalendar()
        summary[(year, week)] += 1
    return dict(summary)

def get_monthly_summary(logs):
    from collections import defaultdict
    import datetime
    summary = defaultdict(int)
    for date_str in logs:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        summary[(dt.year, dt.month)] += 1
    return dict(summary)

def detect_milestones(logs, custom_milestones=None):
    streaks = []
    if not logs:
        return streaks
    logs = sorted(logs)
    from datetime import datetime, timedelta
    streak = 1
    max_streak = 1
    prev = datetime.strptime(logs[0], '%Y-%m-%d')
    milestones = custom_milestones if custom_milestones else [7, 14, 21, 30, 60, 90, 180, 365]
    achieved = set()
    for i in range(1, len(logs)):
        curr = datetime.strptime(logs[i], '%Y-%m-%d')
        if (curr - prev).days == 1:
            streak += 1
        else:
            streak = 1
        prev = curr
        max_streak = max(max_streak, streak)
        for m in milestones:
            if streak == m and m not in achieved:
                streaks.append(f"{m}-day streak")
                achieved.add(m)
    return streaks

@app.route('/export/json')
def export_json():
    data = load_habits()
    response = make_response(json.dumps(data, indent=2))
    response.headers['Content-Disposition'] = 'attachment; filename=habits.json'
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/export/csv')
def export_csv():
    data = load_habits()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Habit Name', 'Type', 'Start Date', 'Target', 'Date', 'Status', 'Journal'])
    for habit in data['habits']:
        logs = habit.get('logs', [])
        failures = habit.get('failures', [])
        journal = habit.get('journal', {})
        for date in set(logs + failures + list(journal.keys())):
            status = 'Done' if date in logs else ('Failed' if date in failures else '')
            entry = journal.get(date, '')
            writer.writerow([habit['name'], habit['type'], habit['start_date'], habit['target'], date, status, entry])
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=habits.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/toggle_dark_mode')
def toggle_dark_mode():
    resp = make_response(redirect(request.referrer or url_for('dashboard')))
    current = request.cookies.get('dark_mode', '0')
    resp.set_cookie('dark_mode', '1' if current == '0' else '0', max_age=60*60*24*365)
    return resp

@app.route('/weekly_digest')
def weekly_digest():
    data = load_habits()
    from datetime import datetime, timedelta
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    summary = []
    for habit in data['habits']:
        logs = [d for d in habit.get('logs', []) if week_ago.strftime('%Y-%m-%d') <= d <= today.strftime('%Y-%m-%d')]
        failures = [d for d in habit.get('failures', []) if week_ago.strftime('%Y-%m-%d') <= d <= today.strftime('%Y-%m-%d')]
        summary.append({
            'name': habit['name'],
            'type': habit['type'],
            'done': len(logs),
            'failed': len(failures),
            'streaks': detect_milestones(logs)
        })
    return render_template('weekly_digest.html', summary=summary)

@app.route('/archive/<habit_id>', methods=['POST'])
def archive_habit(habit_id):
    data = load_habits()
    for habit in data['habits']:
        if habit['id'] == habit_id:
            habit['archived'] = True
            break
    save_habits(data)
    return redirect(url_for('dashboard'))

@app.route('/restore/<habit_id>', methods=['POST'])
def restore_habit(habit_id):
    data = load_habits()
    for habit in data['habits']:
        if habit['id'] == habit_id:
            habit['archived'] = False
            break
    save_habits(data)
    return redirect(url_for('dashboard'))

@app.route('/edit/<habit_id>', methods=['GET', 'POST'])
def edit_habit(habit_id):
    data = load_habits()
    habit = next((h for h in data['habits'] if h['id'] == habit_id), None)
    if not habit:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        habit['name'] = request.form['name']
        habit['type'] = request.form['type']
        habit['target'] = request.form['target']
        habit['start_date'] = request.form['start_date']
        habit['notes'] = request.form.get('notes', '')
        habit['tags'] = [t.strip() for t in request.form.get('tags', '').split(',') if t.strip()]
        milestones = request.form.get('milestones', '')
        if milestones:
            habit['custom_milestones'] = [int(m.strip()) for m in milestones.split(',') if m.strip().isdigit()]
        else:
            habit['custom_milestones'] = []
        save_habits(data)
        return redirect(url_for('dashboard'))
    return render_template('edit_habit.html', habit=habit)

if __name__ == '__main__':
    app.run(debug=True) 