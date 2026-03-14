# app.py — Industrial Predictive Maintenance System
# Render-ready | Flask Backend | ML-powered

import os, io
from datetime import datetime
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, flash, send_file)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from flask_mail import Mail, Message

from config import Config
from auth   import init_db, get_user_by_id, verify_user, get_all_users, create_user, delete_user
from models import (MACHINES, predict_machine, generate_daily_report,
                    generate_analytics_data, get_live_data,
                    generate_sensor_history, MODEL_METRICS)

# ── APP SETUP ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

# Create instance folder for local dev
if not os.environ.get('RENDER'):
    os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

init_db()

login_manager = LoginManager(app)
login_manager.login_view    = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'

mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# ── AUTH ───────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('dashboard') if current_user.is_authenticated else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = verify_user(request.form.get('username','').strip(),
                           request.form.get('password',''))
        if user:
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ── DASHBOARD ──────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    machine_ids = ([current_user.assigned_machine]
                   if current_user.role == 'operator' and current_user.assigned_machine
                   else list(MACHINES.keys()))
    daily_report  = generate_daily_report()
    predictions   = {mid: predict_machine(mid) for mid in machine_ids}
    selected_id   = request.args.get('machine', machine_ids[0])
    if selected_id not in predictions:
        selected_id = machine_ids[0]
    selected_pred = predictions[selected_id]
    history       = generate_sensor_history(selected_id)
    return render_template('dashboard.html',
        machines=MACHINES, machine_ids=machine_ids,
        predictions=predictions, selected_id=selected_id,
        selected_pred=selected_pred, history=history,
        daily_report=daily_report, model_metrics=MODEL_METRICS,
        now=datetime.now().strftime("%A, %d %B %Y — %H:%M")
    )

# ── SEARCH ─────────────────────────────────────────────────────────────────────
@app.route('/search')
@login_required
def search():
    mid     = request.args.get('machine_id','').upper().strip()
    result  = None
    history = None
    if mid:
        if mid in MACHINES:
            result  = predict_machine(mid)
            history = generate_sensor_history(mid)
        else:
            flash(f'Machine ID "{mid}" not found.', 'warning')
    return render_template('search.html', result=result, history=history,
                           machines=MACHINES, query=mid)

# ── ANALYTICS ──────────────────────────────────────────────────────────────────
@app.route('/analytics')
@login_required
def analytics():
    if not (current_user.can('view_costs') or current_user.can('generate_reports')):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('analytics.html',
        analytics=generate_analytics_data(),
        predictions={mid: predict_machine(mid) for mid in MACHINES}
    )

# ── USER MANAGEMENT ────────────────────────────────────────────────────────────
@app.route('/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('users.html', users=get_all_users(), machines=MACHINES)

@app.route('/users/create', methods=['POST'])
@login_required
def create_user_route():
    if current_user.role != 'admin':
        return jsonify({"success": False}), 403
    ok, msg = create_user(
        request.form.get('username'),
        request.form.get('password'),
        request.form.get('role'),
        request.form.get('email'),
        request.form.get('assigned_machine') or None
    )
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('manage_users'))

@app.route('/users/delete/<int:uid>', methods=['POST'])
@login_required
def delete_user_route(uid):
    if current_user.role != 'admin':
        return jsonify({"success": False}), 403
    delete_user(uid)
    flash('User deleted.', 'success')
    return redirect(url_for('manage_users'))

# ── PDF REPORT ─────────────────────────────────────────────────────────────────
@app.route('/report/pdf/<machine_id>')
@login_required
def download_pdf(machine_id):
    if machine_id not in MACHINES:
        flash('Machine not found.', 'warning')
        return redirect(url_for('dashboard'))
    pred = predict_machine(machine_id)
    return send_file(
        io.BytesIO(_build_pdf(pred)),
        download_name=f"HealthReport_{machine_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
        as_attachment=True, mimetype='application/pdf'
    )

def _build_pdf(pred):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    H    = ParagraphStyle('H',  fontSize=20, textColor=colors.HexColor('#00d4ff'), fontName='Helvetica-Bold', spaceAfter=4)
    Sub  = ParagraphStyle('Sub',fontSize=10, textColor=colors.HexColor('#888888'), spaceAfter=10)
    Sec  = ParagraphStyle('Sec',fontSize=13, textColor=colors.HexColor('#0a5c9e'), fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    Body = ParagraphStyle('B',  fontSize=10, spaceAfter=5)
    Foot = ParagraphStyle('F',  fontSize=8,  textColor=colors.grey, alignment=1)

    def tbl(data, cw, bg):
        t = Table(data, colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,-1),bg),
            ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),10),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white,colors.HexColor('#f9f9f9')]),
            ('PADDING',(0,0),(-1,-1),6),
        ]))
        return t

    c   = pred['cost_estimate']
    mid = pred['machine_id']
    story = [
        Paragraph("Industrial Predictive Maintenance System", H),
        Paragraph(f"Machine Health Report — {datetime.now().strftime('%d %B %Y, %H:%M')}", Sub),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor('#00d4ff')),
        Spacer(1,0.3*cm),
        Paragraph("Machine Information", Sec),
        tbl([["Machine ID",mid],["Name",pred['machine_info']['name']],
             ["Operator",pred['machine_info']['operator']],
             ["Location",pred['machine_info']['location']],
             ["Installed",pred['machine_info']['installation_date']],
             ["Last Maintenance",pred['machine_info']['last_maintenance']]],
            [5*cm,12*cm], colors.HexColor('#e8f4fd')),
        Spacer(1,0.3*cm),
        Paragraph("Health & Prediction", Sec),
        tbl([["Health Score",f"{pred['health_score']}%"],
             ["Failure Probability",f"{pred['failure_probability']}%"],
             ["Status",pred['status']],
             ["Anomaly Detected","YES" if pred['is_anomaly'] else "NO"],
             ["Remaining Useful Life",f"{pred['rul_days']} days"]] +
            ([["Suggested Maintenance",pred['suggested_maintenance_date']]]
             if pred.get('suggested_maintenance_date') else []),
            [6*cm,11*cm], colors.HexColor('#fff3e0')),
        Spacer(1,0.3*cm),
        Paragraph("Failure Deduction & Recommendations", Sec),
        Paragraph(f"<b>Failure Type:</b> {pred['failure_type']}", Body),
        Paragraph(f"<b>Root Cause:</b> {pred['root_cause']}", Body),
        *[Paragraph(f"  {i}. {s}", Body) for i,s in enumerate(pred['solutions'],1)],
        Spacer(1,0.3*cm),
        Paragraph("Maintenance Cost Estimation (INR)", Sec),
        tbl([["Spare Parts Cost",f"Rs.{c['spare_parts_cost']:,}"],
             ["Labor Cost",f"Rs.{c['labor_cost']:,}"],
             ["Total Estimated",f"Rs.{c['total_estimated']:,}"],
             ["Preventive Maint.",f"Rs.{c['preventive_cost']:,}"],
             ["Breakdown Repair",f"Rs.{c['breakdown_repair']:,}"],
             ["Estimated Savings",f"Rs.{c['estimated_savings']:,}"]],
            [8*cm,9*cm], colors.HexColor('#e8f8e8')),
        Spacer(1,0.8*cm),
        HRFlowable(width="100%",thickness=0.5,color=colors.grey),
        Paragraph("Confidential — Industrial Predictive Maintenance System", Foot),
    ]
    doc.build(story)
    buf.seek(0)
    return buf.read()

# ── API ────────────────────────────────────────────────────────────────────────
@app.route('/api/live-data')
@login_required
def api_live_data():
    mid = request.args.get('machine_id','MCH-101')
    if mid not in MACHINES:
        return jsonify({"error":"Machine not found"}), 404
    data = get_live_data(mid)
    pred = predict_machine(mid)
    data.update({
        "failure_probability": pred["failure_probability"],
        "health_score":        pred["health_score"],
        "rul_days":            pred["rul_days"],
        "status":              pred["status"],
        "is_anomaly":          pred["is_anomaly"],
    })
    return jsonify(data)

@app.route('/api/predictions')
@login_required
def api_predictions():
    return jsonify({mid: predict_machine(mid) for mid in MACHINES})

@app.route('/api/machine/<machine_id>')
@login_required
def api_machine(machine_id):
    if machine_id not in MACHINES:
        return jsonify({"error":"Not found"}), 404
    return jsonify({
        "prediction": predict_machine(machine_id),
        "history":    generate_sensor_history(machine_id)
    })

@app.route('/api/send-alert/<machine_id>', methods=['POST'])
@login_required
def send_alert(machine_id):
    pred = predict_machine(machine_id)
    body = (f"INDUSTRIAL ALERT — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Machine ID:   {machine_id}\n"
            f"Failure Type: {pred['failure_type']}\n"
            f"Risk:         {pred['failure_probability']}%\n"
            f"Root Cause:   {pred['root_cause']}\n\n"
            + '\n'.join(f"  - {s}" for s in pred['solutions']))
    print(f"\n{'='*60}\n EMAIL ALERT\n{body}\n{'='*60}")
    try:
        msg = Message(f"CRITICAL: {machine_id} — {pred['failure_type']}",
                      recipients=[Config.ALERT_RECIPIENT])
        msg.body = body
        mail.send(msg)
        return jsonify({"success":True,"method":"email"})
    except Exception:
        return jsonify({"success":True,"method":"console_simulation"})

# ── RUN ────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*60}")
    print("  Industrial Predictive Maintenance System")
    print(f"  Running on port {port}")
    print("  Login: admin / Admin@123")
    print(f"{'='*60}\n")
    app.run(debug=False, host='0.0.0.0', port=port)
