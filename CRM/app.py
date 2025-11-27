from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from database import db, init_db
from models import Customer, Order
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
init_db(app)

# Главная страница - список клиентов
@app.route('/')
def index():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    if search_query:
        customers = Customer.query.filter(
            db.or_(
                Customer.last_name.ilike(f'%{search_query}%'),
                Customer.first_name.ilike(f'%{search_query}%'),
                Customer.email.ilike(f'%{search_query}%'),
                Customer.phone.ilike(f'%{search_query}%')
            )
        ).paginate(page=page, per_page=10, error_out=False)
    else:
        customers = Customer.query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('customers.html', customers=customers, search_query=search_query)

# Добавление нового клиента
@app.route('/customer/new', methods=['GET', 'POST'])
def new_customer():
    if request.method == 'POST':
        try:
            # Валидация данных
            last_name = request.form['last_name'].strip()
            first_name = request.form['first_name'].strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            registration_date_str = request.form.get('registration_date', '')
            notes = request.form.get('notes', '').strip()
            
            # Проверка обязательных полей
            if not last_name or not first_name:
                flash('Фамилия и имя являются обязательными полями', 'error')
                return render_template('customer_form.html')
            
            # Проверка email
            if email and '@' not in email:
                flash('Введите корректный email адрес', 'error')
                return render_template('customer_form.html')
            
            # Парсинг даты
            if registration_date_str:
                try:
                    registration_date = datetime.strptime(registration_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Неверный формат даты. Используйте формат ГГГГ-ММ-ДД', 'error')
                    return render_template('customer_form.html')
            else:
                registration_date = datetime.utcnow().date()
            
            customer = Customer(
                last_name=last_name,
                first_name=first_name,
                middle_name=request.form.get('middle_name', '').strip(),
                email=email,
                phone=phone,
                registration_date=registration_date,
                notes=notes
            )
            
            db.session.add(customer)
            db.session.commit()
            flash('Клиент успешно добавлен', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении клиента: {str(e)}', 'error')
    
    return render_template('customer_form.html')

# Редактирование клиента
@app.route('/customer/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        try:
            # Валидация данных
            last_name = request.form['last_name'].strip()
            first_name = request.form['first_name'].strip()
            email = request.form.get('email', '').strip()
            
            if not last_name or not first_name:
                flash('Фамилия и имя являются обязательными полями', 'error')
                return render_template('customer_form.html', customer=customer)
            
            if email and '@' not in email:
                flash('Введите корректный email адрес', 'error')
                return render_template('customer_form.html', customer=customer)
            
            customer.last_name = last_name
            customer.first_name = first_name
            customer.middle_name = request.form.get('middle_name', '').strip()
            customer.email = email
            customer.phone = request.form.get('phone', '').strip()
            customer.notes = request.form.get('notes', '').strip()
            
            db.session.commit()
            flash('Данные клиента успешно обновлены', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении данных: {str(e)}', 'error')
    
    return render_template('customer_form.html', customer=customer)

# Удаление клиента
@app.route('/customer/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()
        flash('Клиент успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении клиента: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# Управление заказами клиента
@app.route('/customer/<int:customer_id>/orders')
def customer_orders(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('orders.html', customer=customer)

# Добавление заказа
@app.route('/customer/<int:customer_id>/order/new', methods=['POST'])
def new_order(customer_id):
    try:
        product_name = request.form['product_name'].strip()
        quantity = request.form['quantity']
        price = request.form['price']
        
        if not product_name or not quantity or not price:
            flash('Все поля заказа обязательны для заполнения', 'error')
            return redirect(url_for('customer_orders', customer_id=customer_id))
        
        order = Order(
            customer_id=customer_id,
            product_name=product_name,
            quantity=int(quantity),
            price=float(price),
            status=request.form.get('status', 'Новый'),
            notes=request.form.get('notes', '').strip()
        )
        
        db.session.add(order)
        db.session.commit()
        flash('Заказ успешно добавлен', 'success')
        
    except ValueError:
        flash('Количество и цена должны быть числовыми значениями', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении заказа: {str(e)}', 'error')
    
    return redirect(url_for('customer_orders', customer_id=customer_id))

# Удаление заказа
@app.route('/order/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        customer_id = order.customer_id
        db.session.delete(order)
        db.session.commit()
        flash('Заказ успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении заказа: {str(e)}', 'error')
    
    return redirect(url_for('customer_orders', customer_id=customer_id))

# Генерация отчетов
@app.route('/reports')
def reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Customer.query
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Customer.registration_date >= start_date)
        except ValueError:
            flash('Неверный формат начальной даты', 'error')
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Customer.registration_date <= end_date)
        except ValueError:
            flash('Неверный формат конечной даты', 'error')
    
    customers = query.all()
    
    # Статистика
    total_customers = len(customers)
    total_orders = sum(len(customer.orders) for customer in customers)
    total_revenue = sum(
        sum(order.quantity * order.price for order in customer.orders)
        for customer in customers
    )
    
    return render_template('reports.html', 
                         customers=customers,
                         total_customers=total_customers,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         start_date=start_date,
                         end_date=end_date)

# API для поиска клиентов
@app.route('/api/customers/search')
def api_customer_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    customers = Customer.query.filter(
        db.or_(
            Customer.last_name.ilike(f'%{query}%'),
            Customer.first_name.ilike(f'%{query}%'),
            Customer.email.ilike(f'%{query}%'),
            Customer.phone.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'name': f'{customer.last_name} {customer.first_name} {customer.middle_name or ""}',
            'email': customer.email,
            'phone': customer.phone
        })
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
    