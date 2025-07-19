from flask import render_template, redirect, url_for, request, flash, current_app, jsonify,session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, extract, or_
from ..models import *
from datetime import datetime,timedelta
import calendar
from flask_login import login_required, current_user, logout_user,  LoginManager # type: ignore
from . import admin
from ..forms import *
from ..models import db
import os
from application.auth import *
import secrets
from PIL import Image
from flask import current_app
import plotly.graph_objs as go # type: ignore
import plotly.offline as plot # type: ignore



def save_product_picture(file):
    # Set the desired size for resizing
    size = (300, 300)

    # Generate a random hex string for the filename
    random_hex = secrets.token_hex(9)

    # Get the file extension
    _, f_ex = os.path.splitext(file.filename)


    # Generate the final filename (random + extension)
    post_img_fn = random_hex + f_ex

    # Define the path to save the file (UPLOAD_PRODUCTS should be configured in your Flask app)
    post_image_path = os.path.join(current_app.root_path, current_app.config['UPLOAD_PRODUCTS'], post_img_fn)

    try:
        # Open the image
        img = Image.open(file)

        # Resize the image to fit within the size (thumbnail)
        img.thumbnail(size)

        # Save the resized image
        img.save(post_image_path)

        return post_img_fn  # Return the filename to store in the database
    except Exception as e:
        # If an error occurs during image processing, handle it
        print(f"Error saving image: {e}")
        return None

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.newlogin'

@login_manager.user_loader
def load_user(user_id):
    user_type = session.get('user_type')
    if user_type == 'pharmacy':
        if Pharmacy.query.get(int(user_id)):
            return Pharmacy.query.get(int(user_id))
        else:
            return Staff.query.get(int(user_id))
    elif user_type == 'customer':
        return User.query.get(int(user_id))
    elif user_type == 'delivery_guy':
        return DeliveryGuy.query.get(int(user_id))

    return None


@admin.route('/admindash', methods=["GET", "POST"])
def admindash():
    pending_pharmacy = Pharmacy.query.filter(Pharmacy.verified == False).all()
    count = len(pending_pharmacy)
    today = datetime.today()
    current_month, current_year = today.month, today.year
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_of_month = next_month - timedelta(seconds=1)
    start_of_year = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_year = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)

    total_sales = db.session.query(func.sum((Sales.price*0.18)*Sales.quantity)).scalar() or 0.0

    daily_sales = db.session.query(
            func.date(Sales.date_).label('date'),
            func.sum(((Sales.price *0.18)* Sales.quantity)).label('total')
        ).group_by(func.date(Sales.date_)).order_by(
            func.date(Sales.date_)).all() or 0.0
    total_monthly_sales = db.session.query(func.sum((Sales.price *0.18) * Sales.quantity)).filter(
            Sales.date_ >= start_of_month, Sales.date_ <= end_of_month).scalar() or 0.0

    total_annual_sales = db.session.query(func.sum((Sales.price *0.18)* Sales.quantity)).filter(
            Sales.date_ >= start_of_year, Sales.date_ <= end_of_year).scalar() or 0.0

    today_sales = db.session.query(func.sum((Sales.price *0.18)* Sales.quantity)).filter(
            func.date(Sales.date_) == today.date()).scalar() or 0.0    

    return render_template('admin/admindash.html', count=count, daily_sales=daily_sales,
                           total_annual_sales=total_annual_sales, total_monthly_sales=total_monthly_sales,
                           today_sales=today_sales, total_sales=total_sales)

@admin.route('/verify pharmacy/<int:pharmacy_id>', methods=["GET", "POST"])
def verifypharmacy(pharmacy_id):
    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)
    if pharmacy:
        pharmacy.verified = True
        db.session.add(pharmacy)
    try:
        db.session.commit()
        flash('Pharmacy Verified.')
        return redirect(url_for('admin.pending_verification'))
    except IntegrityError:
        flash('Pharmacies failed due to integrity.')
        return redirect(url_for('admin.pending_verification'))

@admin.route('/cancelled pharmacy/<int:pharmacy_id>')
def cancel_pharmacy(pharmacy_id):
    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)
    if pharmacy:
        db.session.delete(pharmacy)
        db.session.commit()
        return redirect(url_for('admin.pending_verification'))
    else:
        flash('Pharmacy could not be found')
        return redirect(url_for('admin.pending_verification'))

@admin.route('/registered pharmacies')
def registered_pharmacies():
    pharmacies = Pharmacy.query.filter(Pharmacy.verified == True, Pharmacy.confirmed == True).all()
    return render_template('admin/registereduser.html', pharmacies=pharmacies)

@admin.route('/register_pharmacy')
def register_pharmacy():
    form = PharmacyRegistrationForm()
    return render_template('auth/registerphar.html', form=form)

@admin.route('/pending vefication')
def pending_verification():
    pharmacies = Pharmacy.query.filter(Pharmacy.verified == False).all()
    return render_template('admin/pendingpharmacies.html', pharmacies=pharmacies)