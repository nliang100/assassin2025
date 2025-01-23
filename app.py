import os
from flask import Flask, request, render_template, redirect, url_for, send_file
import pandas as pd
import smtplib
from email.message import EmailMessage
import ssl

app = Flask(__name__)

# Path to store the uploaded CSV
UPLOAD_FOLDER = "uploaded_data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists
CSV_FILE = os.path.join(UPLOAD_FOLDER, "player_data.csv")

# Global variable to store player data
data = None

EMAIL_SENDER = 'andover2025@gmail.com'  # Replace with your email
EMAIL_PASSWORD = 'wtwz fdsj bxrl niyb'  # Replace with your app password

@app.route('/')
def index():
    global data
    uploaded_file = None
    if os.path.exists(CSV_FILE):
        uploaded_file = os.path.basename(CSV_FILE)
        if data is None:
            data = pd.read_csv(CSV_FILE)
    return render_template('index.html', data=data.to_html() if data is not None else None, uploaded_file=uploaded_file)


@app.route('/upload', methods=['POST'])
def upload_file():
    global data
    file = request.files['file']
    if file:
        # Save the uploaded file
        file.save(CSV_FILE)
        data = pd.read_csv(CSV_FILE)  # Load the data into memory
    return render_template('upload_success.html', data=data.to_html())

@app.route('/kill', methods=['POST'])
def process_kill():
    global data
    if data is None:
        return "No data available. Please upload a dataset first."

    killer = request.form['killer']
    if killer not in data['Names'].values:
        return "Killer not found in the dataset."

    data.reset_index(drop=True, inplace=True)
    killer_index = data.index[data['Names'] == killer][0]
    victim_index = (killer_index + 1) % len(data)  # The victim is the next in the row
    victim = data.iloc[victim_index]

    # Find the next target after the victim
    next_target_index = (victim_index + 1) % len(data)
    next_target = data.iloc[next_target_index]

    # Remove the victim
    data.drop(index=victim_index, inplace=True)
    data.reset_index(drop=True, inplace=True)

    # Save the updated dataset
    data.to_csv(CSV_FILE, index=False)

    # Send email to the killer about their next target
    killer_email = data.loc[data['Names'] == killer, 'Emails'].values[0]
    send_email(killer, next_target['Names'], killer_email)

    return render_template('kill_confirmation.html')



@app.route('/data')
def view_data():
    global data
    if data is None:
        return "No data available. Please upload a dataset first."
    return render_template('data.html', data=data.to_html())

def send_email(killer_name, target_name, recipient_email):
    subject = 'Your Next Assassin Target'
    body = f"Hi {killer_name},\n\nYour next target is {target_name}. Have fun and good luck!"

    em = EmailMessage()
    em['From'] = EMAIL_SENDER
    em['To'] = recipient_email
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(em)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

