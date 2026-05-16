from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from collections import Counter
from flask_mail import Mail, Message
import urllib.parse
from datetime import datetime
import random
import requests # Ensure this is at the top of your app.py
import requests
from datetime import datetime



app = Flask(__name__)
app.secret_key = "el_rosie_secret_secure_key"
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
FEEDBACK_DB = []  # <-- ADD THIS LINE HERE

# --- HELPER FUNCTIONS ---
def get_booking_by_id(booking_id):
    # Search through the active bookings list
    for b in BOOKINGS_DB:
        if str(b.get('id')) == str(booking_id): # Use str() to prevent type mismatches
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

import urllib.parse  # Ensure this is at the top of your file
import requests
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for

@app.route('/book', methods=['GET', 'POST'])
def book():
    # --- 1. Weather Fetching for Smart Suggestions ---
    try:
        # Nasugbu location API call
        api_key = "bc58679904d9c02d137021c3272d3f9e"
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Nasugbu&appid={api_key}&units=metric"
        data = requests.get(url, timeout=5).json()
        
        temp = round(data['main']['temp'])
        condition = data['weather'][0]['main']
        
        if condition == "Rain":
            rec_text = "It's a bit rainy today! Perfect for an indoor Spa session or a cozy day in your bungalow."
            rec_icon = "cloud-showers-heavy"
        elif temp > 30:
            rec_text = "It's a beautiful sunny day! We recommend adding a Pool Pass or an Extra Cooler."
            rec_icon = "sun"
        else:
            rec_text = "The weather is perfect for a sunset walk. Enjoy your stay!"
            rec_icon = "palmtree"
            
        weather_rec = {"text": rec_text, "icon": rec_icon, "temp": temp}
    except:
        # Fallback if API fails
        weather_rec = {"text": "Welcome back! We are ready for your stay.", "icon": "heart", "temp": "30"}

    # --- 2. Room Availability Logic ---
    total_cost = 0
    days = 0
    selected_room_id = None
    qr_code_url = None
    
    availability = {rid: r['total_inventory'] for rid, r in ROOM_PRICES.items()}
    for b in BOOKINGS_DB:
        for rid, r in ROOM_PRICES.items():
            if b['room'] == r['name']:
                availability[rid] -= 1

    # --- 3. Handling the Booking Submission ---
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

        # Final Confirmation Logic
        if request.form.get('confirm_booking') == 'true':
            if availability.get(room_type, 0) <= 0:
                flash("Sorry, that room type is fully booked!", "danger")
                return redirect(url_for('book'))

            # Unique Booking ID
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
            
            # --- START DYNAMIC QR CODE ATTACHMENT ---
            # Automatically detects your domain (works on local machine and Render)
            base_url = request.host_url.rstrip('/') 

            # Build the link that will be stored in the QR code
            checkin_link = f"{base_url}/scan/{booking_id}"

            # Safely encode the link and call the QR generator API
            encoded_link = urllib.parse.quote(checkin_link)
            qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_link}"
            # --- END DYNAMIC QR CODE ATTACHMENT ---

            # Send the email with all the details
            send_confirmation_email(
                guest_email, 
                guest_name, 
                booking_id, 
                booking_record['room'], 
                total_cost, 
                special_notes
            )
            
            flash(f"Success! A confirmation email has been sent to {guest_email}.", "success")

    # --- 4. Render the Page ---
    return render_template('booking.html', 
                           room_prices=ROOM_PRICES, 
                           total_cost=total_cost, 
                           days=days, 
                           selected_room=selected_room_id, 
                           qr_code_url=qr_code_url,
                           availability=availability,
                           weather=weather_rec)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        # Check if this specific user has a completed booking in history that hasn't been reviewed yet
        user_email = session.get('user')
        for h in BOOKING_HISTORY:
            if h.get('email') == user_email and h.get('status') == 'Checked-Out' and not h.get('reviewed'):
                return redirect(url_for('leave_review', booking_id=h.get('id')))

        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('book'))
    

@app.route('/review/<booking_id>', methods=['GET', 'POST'])
def leave_review(booking_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment', '')
        user_email = session.get('user')
        
        # Mark the booking record as reviewed so they aren't trapped in a prompt loop
        for h in BOOKING_HISTORY:
            if h.get('id') == booking_id:
                h['reviewed'] = True
                
        # Save review details
        review_record = {
            "booking_id": booking_id,
            "email": user_email,
            "rating": int(rating),
            "comment": comment,
            "date": datetime.now().strftime("%Y-%m-%d %I:%M %p")
        }
        FEEDBACK_DB.append(review_record)
        
        flash("Thank you for your valuable feedback! Hope to see you again.", "success")
        return redirect(url_for('book'))
        
    return render_template('review.html', booking_id=booking_id)

import requests
from collections import Counter

@app.route('/explore')
def explore():
    # Complete structural dataset needed for Jinja loops
    resort_guide = {
        "amenities": [
            {"title": "🏊 Infinity Pool", "hours": "6:00 AM - 10:00 PM", "rules": "Proper swimwear required. No glassware near the deck."},
            {"title": "💆 El Rosie Wellness Spa", "hours": "9:00 AM - 8:00 PM", "rules": "Prior appointment booking recommended via front desk."},
            {"title": "🍹 Beachfront Bar & Grill", "hours": "11:00 AM - 12:00 AM", "rules": "Happy hours track daily from 4:00 PM to 6:00 PM."}
        ],
        "menus": {
            "breakfast": ["Filipino Silog Plates (₱250)", "Fluffy Pancakes with Mango Syrup (₱180)", "Fresh Brewed Kapeng Barako (₱90)"],
            "dinner": ["Signature Grilled Seafood Platter (₱850)", "Crispy Pork Belly Lechon (₱420)", "Tropical Mango Graham Shakes (₱150)"]
        }
    }
    # CRITICAL: Pass resort_guide as 'guide' so explore.html can read it!
    return render_template('explore.html', guide=resort_guide)
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') == 'admin':
        # --- Revenue and Reservation Analytics ---
        total_revenue = sum(b['total_paid'] for b in BOOKINGS_DB) + sum(b['total_paid'] for b in BOOKING_HISTORY)
        total_bookings = len(BOOKINGS_DB) + len(BOOKING_HISTORY)
        recent_history = BOOKING_HISTORY[::-1] 
        
        # --- Popular Room Trackers ---
        room_list = [b['room'] for b in BOOKINGS_DB] + [b['room'] for b in BOOKING_HISTORY]
        popular_room = Counter(room_list).most_common(1)[0][0] if room_list else "None"
        
        # --- NEW: Live Guest Occupancy Counting Metrics ---
        # 1. Count guests currently marked active "In-Resort" or "Checked-In"
        in_resort_count = sum(1 for b in BOOKINGS_DB if b.get('status') in ['In-Resort', 'Checked-In'])
        
        # 2. Count incoming bookings today that are confirmed or pending arrivals
        expected_today = sum(1 for b in BOOKINGS_DB if b.get('status') in ['Confirmed', 'Pending'])
        
        # --- Weather Integration ---
        try:
            # Using Nasugbu as the location for El Rosie
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

        # Return and pass all synchronized analytical parameters to your dashboard template
        return render_template('admin_dashboard.html', 
                               active_bookings=BOOKINGS_DB,
                               bookings=BOOKINGS_DB,
                               history=recent_history,
                               revenue=total_revenue,
                               count=total_bookings, 
                               in_resort=in_resort_count, 
                               expected=expected_today,
                               popular=popular_room,
                               weather=weather_info)
                               
    return redirect(url_for('login'))

@app.route('/catalog')
def catalog():
    # Structural rates directory passed dynamically
    catalog_data = {
        "pool_access": [
            {"type": "Day Swim (8:00 AM - 5:00 PM)", "adult": "₱150", "child": "₱100"},
            {"type": "Night Swim (6:00 PM - 12:00 AM)", "adult": "₱200", "child": "₱120"}
        ],
        "cottages": [
            {"name": "Nipa Hut Cottage (Small)", "capacity": "6-8 Pax", "rate": "₱800"},
            {"name": "Bamboo Pavilion (Medium)", "capacity": "12-15 Pax", "rate": "₱1,500"},
            {"name": "Executive Poolside Cabana", "capacity": "20 Pax", "rate": "₱3,000"}
        ],
        "corkage_fees": [
            {"item": "Local Beers / Hard Liquor", "fee": "₱200 per case"},
            {"item": "Catering / Outside Food Setup", "fee": "₱500 flat rate"},
            {"item": "Whole Lechon / Roasted Pig", "fee": "₱300 per item"}
        ]
    }
    return render_template('catalog.html', catalog=catalog_data)

@app.route('/authorize_staff/<secret>')
def authorize_staff(secret):
    if secret == STAFF_SECRET_CODE:
        session.permanent = True
        session['staff_verified'] = STAFF_SECRET_CODE
        return "<h1>✅ Device Authorized</h1><p>This phone is now a master scanner for 31 days.</p>"
    return "Invalid Secret", 401

@app.route('/scan/<booking_id>')
def scan_qr(booking_id):
    # 1. Verification Check
    is_admin = session.get('admin_logged_in')
    is_staff_verified = session.get('staff_verified') == STAFF_SECRET_CODE

    if not is_admin and not is_staff_verified:
        return "DEBUG: Access Denied. Please visit the unlock link first.", 403
    
    # 2. Retrieve Booking
    booking = get_booking_by_id(booking_id) 
    if not booking:
        return f"DEBUG: Booking {booking_id} Not Found", 404

    current_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    try:
        # CHECK-IN LOGIC
        if booking['status'] == 'Pending':
            booking['status'] = 'Checked-In'
            booking['check_in_time'] = current_time
            
            if is_admin:
                return redirect('/admin/dashboard')
            return f"SUCCESS: {booking['name']} is now Checked-In."
                
        # CHECK-OUT LOGIC (Add the logic below)
        elif booking['status'] == 'Checked-In':
            # Create a copy for history and update status
            checkout_entry = booking.copy()
            checkout_entry['status'] = 'Checked-Out'
            checkout_entry['check_out_time'] = current_time
            
            # Find and remove from active list, then add to history
            found = False
            for item in BOOKINGS_DB:
                if item.get('id') == booking_id:
                    BOOKINGS_DB.remove(item)
                    BOOKING_HISTORY.append(checkout_entry)
                    found = True
                    break
            
            if found:
                print(f"DEBUG: {booking['name']} moved to history.")
                if is_admin:
                    return redirect('/admin/dashboard')
                return f"SUCCESS: {booking['name']} is now Checked-Out."
            else:
                return "ERROR: Booking not found in active list for removal.", 500
        
        return f"Status is {booking['status']}. No action taken."

    except Exception as e:
        return f"CRASH: {e}", 500
    
@app.route('/admin/scanner')
def admin_scanner():
    # This renders the camera interface for the admin
    return render_template('admin_scanner.html')

@app.route('/admin/unlock-secret')
def admin_unlock():
    session['admin_logged_in'] = True
    return "Admin Access Granted!"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)