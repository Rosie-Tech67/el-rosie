from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from collections import Counter
from flask_mail import Mail, Message
import urllib.parse
from datetime import datetime
import random
import os


app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'el_rosie_local_dev_key')

app.permanent_session_lifetime = timedelta(days=31)

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'rosenelcasabal030807@gmail.com'
app.config['MAIL_PASSWORD'] = 'mmuk oyzp ortm susv' 
app.config['MAIL_DEFAULT_SENDER'] = 'rosenelcasabal030807@gmail.com'

mail = Mail(app)

# --- CONFIGURATION ---
STAFF_SECRET_CODE = "rosie_admin_2026"

ROOM_PRICES = {
    "deluxe": {"name": "Deluxe Bungalow: A private retreat (₱3500)", "price": 3500, "total_inventory": 5},
    "ocean_modern": {"name": "Ocean View Suite: Modern comfort (₱3500)", "price": 3500, "total_inventory": 5},
    "ocean_meter": {"name": "Ocean View Suite: Meter rootot (₱3900)", "price": 3900, "total_inventory": 5},
    "spa_villa": {"name": "Spa Villa: Ultimate relaxation (₱2590)", "price": 2590, "total_inventory": 5},
    "beachfront_glamping": {"name": "Beachfront Glamping: Luxury under the stars (₱1800)", "price": 1800, "total_inventory": 5},
    "family_garden": {"name": "Family Garden Villa: Spacious space for loved ones (₱4500)", "price": 4500, "total_inventory": 5},
    "presidential_penthouse": {"name": "Presidential Penthouse: The ultimate elite escape (₱7500)", "price": 7500, "total_inventory": 5},
    
    # --- ADD YOUR NEW ROOMS HERE ---
    "garden_cabin": {"name": "Garden Cabin: Nature's Embrace (₱2800)", "price": 2800, "total_inventory": 4},
    "sunset_loft": {"name": "Sunset Loft: Golden Hour Views (₱4200)", "price": 4200, "total_inventory": 3}

}

USER_DATABASE = {
    "moi@gmail.com": {"password": "123", "role": "customer"},
    "admin@gmail.com": {"password": "99", "role": "admin"}
}

BOOKINGS_DB = []
BOOKING_HISTORY = [] 

# --- HELPER FUNCTIONS ---
def get_booking_by_id(b_id):
    for b in BOOKINGS_DB:
        if b['id'] == b_id:
            return b
    return None

def send_confirmation_email(guest_email, guest_name, booking_id, room_name, total_paid, special_notes):
    try:
        msg = Message(f"El Rosie Reservation Confirmed - {booking_id}", recipients=[guest_email])
        msg.body = f"""
        Hello {guest_name},

        Your booking at El Rosie Beach Resort is confirmed! 

        --- DETAILS ---
        Booking ID: {booking_id}
        Room: {room_name}
        Total Paid: ₱{total_paid}
        Special Request: {special_notes}

        Please show your QR code upon arrival at the resort gate.
        We look forward to hosting you!
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f">>> MAIL ERROR: {e}")
        return False

# --- CORE ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/activities')
def activities():
    return render_template('activities.html')

import requests # Ensure this is at the top of your app.py

@app.route('/book', methods=['GET', 'POST'])
def book():
    # --- NEW: Weather Fetching for Smart Suggestions ---
    try:
        # Nasugbu location API call
        api_key = "bc58679904d9c02d137021c3272d3f9e"
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Nasugbu&appid={api_key}&units=metric"
        data = requests.get(url, timeout=5).json()
        
        temp = round(data['main']['temp'])
        condition = data['weather'][0]['main']
        
        # Logic to choose the recommendation
        if condition == "Rain":
            rec_text = "It's a bit rainy today! Perfect for an indoor Spa session or a cozy day in your bungalow."
            rec_icon = "cloud-showers-heavy"
        elif temp > 30:
            rec_text = "It's a beautiful sunny day! We recommend adding a Pool Pass or an Extra Cooler."
            rec_icon = "sun"
        else:
            rec_text = "The weather is perfect for a sunset walk. Enjoy your stay at El Rosie!"
            rec_icon = "palmtree"
            
        weather_rec = {"text": rec_text, "icon": rec_icon, "temp": temp}
    except:
        # Fallback if API fails
        weather_rec = {"text": "Welcome back to El Rosie! We are ready for your stay.", "icon": "heart", "temp": "30"}

    # --- Your Original Logic ---
    total_cost = 0
    days = 0
    selected_room_id = None
    qr_code_url = None
    
    availability = {rid: r['total_inventory'] for rid, r in ROOM_PRICES.items()}
    for b in BOOKINGS_DB:
        for rid, r in ROOM_PRICES.items():
            if b['room'] == r['name']:
                availability[rid] -= 1

    if request.method == 'POST':
        guest_name = request.form.get('guest_name', '')
        guest_phone = request.form.get('guest_phone', '')
        guest_email = request.form.get('guest_email', '')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        room_type = request.form.get('room_type')
        addons = request.form.getlist('addons')
        adults = request.form.get('adults', '1')
        children = request.form.get('children', '0')
        special_notes = request.form.get('special_notes', 'None') 

        selected_room_id = room_type

        try:
            date_in = datetime.strptime(check_in, "%Y-%m-%d")
            date_out = datetime.strptime(check_out, "%Y-%m-%d")
            days = (date_out - date_in).days
        except: 
            days = 0

        if room_type in ROOM_PRICES and days > 0:
            total_cost = (ROOM_PRICES[room_type]['price'] * days) + (len(addons) * 50)

        if request.form.get('confirm_booking') == 'true':
            if availability.get(room_type, 0) <= 0:
                flash("Sorry, that room type is fully booked!", "danger")
                return redirect(url_for('book'))

            booking_id = f"ELR-{1001 + len(BOOKINGS_DB)}"
            
            booking_record = {
                "id": booking_id, 
                "name": guest_name, 
                "phone": guest_phone,
                "email": guest_email, 
                "check_in": check_in, 
                "check_out": check_out,
                "room": ROOM_PRICES[room_type]['name'],
                "guests": f"Adults: {adults}, Children: {children}",
                "total_paid": total_cost, 
                "status": "Pending",
                "notes": special_notes
            }
            BOOKINGS_DB.append(booking_record)
            
            send_confirmation_email(
                guest_email, 
                guest_name, 
                booking_id, 
                booking_record['room'], 
                total_cost, 
                special_notes
            )
            
            checkin_link = f"https://el-rosie.onrender.com/scan/{booking_id}"
            encoded_link = urllib.parse.quote(checkin_link)
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_link}"
            
            flash(f"Success! A confirmation email has been sent.", "success")

    # Pass weather_rec into your render_template
    return render_template('booking.html', 
                           room_prices=ROOM_PRICES, 
                           total_cost=total_cost, 
                           days=days, 
                           selected_room=selected_room_id, 
                           qr_code_url=qr_code_url,
                           availability=availability,
                           weather=weather_rec) # <--- Added this

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if the user exists in your USER_DATABASE
        if email in USER_DATABASE and USER_DATABASE[email]['password'] == password:
            session.permanent = True
            session['user'] = email
            session['role'] = USER_DATABASE[email]['role']
            
            flash(f"Welcome back to El Rosie!", "success")
            
            # --- START OF FIX ---
            # If the user is an admin, send them to the dashboard
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            
            # Otherwise, send regular customers to the home page
            return redirect(url_for('home')) 
            # --- END OF FIX ---
            
        else:
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template('login.html')

import requests
from collections import Counter

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') == 'admin':
        # --- Your Existing Logic ---
        total_revenue = sum(b['total_paid'] for b in BOOKINGS_DB) + sum(b['total_paid'] for b in BOOKING_HISTORY)
        total_bookings = len(BOOKINGS_DB) + len(BOOKING_HISTORY)
        active_guests = len([b for b in BOOKINGS_DB if b['status'] == 'Checked-In'])
        recent_history = BOOKING_HISTORY[::-1] 
        room_list = [b['room'] for b in BOOKINGS_DB] + [b['room'] for b in BOOKING_HISTORY]
        popular_room = Counter(room_list).most_common(1)[0][0] if room_list else "None"
        
        # --- NEW: Weather Integration ---
        try:
            # Using Nasugbu as the location for El Rohi
            api_key = "bc58679904d9c02d137021c3272d3f9e" 
            url = f"http://api.openweathermap.org/data/2.5/weather?q=Nasugbu&appid={api_key}&units=metric"
            data = requests.get(url, timeout=5).json()
            
            temp = round(data['main']['temp'])
            condition = data['weather'][0]['main']
            
            # Smart logic for Admin recommendation
            if condition == "Rain":
                advice = "Expect rain: Suggest indoor spa sessions."
            elif temp > 30:
                advice = "High heat: Ensure pool area is ready."
            else:
                advice = "Good weather: Perfect for beach glamping."

            weather_info = {
                "temp": temp,
                "desc": data['weather'][0]['description'].capitalize(),
                "icon": data['weather'][0]['icon'],
                "advice": advice
            }
        except Exception as e:
            # Fallback so the dashboard doesn't crash if the internet is down
            weather_info = {"temp": "30", "desc": "Sunny", "icon": "01d", "advice": "Standard Operations"}

        return render_template('admin_dashboard.html', 
                               active_bookings=BOOKINGS_DB,
                               history=recent_history,
                               revenue=total_revenue,
                               count=total_bookings, 
                               active=active_guests, 
                               popular=popular_room,
                               weather=weather_info) # Passing new data to HTML
    return redirect(url_for('login'))
@app.route('/authorize_staff/<secret>')
def authorize_staff(secret):
    if secret == STAFF_SECRET_CODE:
        session.permanent = True
        session['staff_verified'] = STAFF_SECRET_CODE
        return "<h1>✅ Device Authorized</h1><p>This phone is now a master scanner for 31 days.</p>"
    return "Invalid Secret", 401

@app.route('/scan/<booking_id>')
def scan_qr(booking_id):
    if session.get('staff_verified') != STAFF_SECRET_CODE:
        return "<h1>⚠️ Access Denied</h1><p>Visit authorization link first.</p>", 403
    
    booking = get_booking_by_id(booking_id) 
    if not booking:
        return "<h1>Error: Booking Not Found</h1>", 404

    current_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    if booking['status'] == 'Pending':
        booking['status'] = 'Checked-In'
        booking['check_in_time'] = current_time
        flash(f"Guest {booking['name']} Checked-In successfully!", "success")
            
    elif booking['status'] == 'Checked-In':
        booking['status'] = 'Checked-Out'
        booking['check_out_time'] = current_time
        
        # Move to history and remove from active list
        BOOKING_HISTORY.append(booking)
        BOOKINGS_DB.remove(booking) 
        flash(f"Guest {booking['name']} Checked-Out successfully!", "info")
            
    return redirect(url_for('admin_dashboard'))



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    # '0.0.0.0' tells Flask to be visible on your local network
    app.run(host='0.0.0.0', port=5000, debug=True)