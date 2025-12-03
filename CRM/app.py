from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
from models import db, Customer, Order

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

# Создание таблиц при первом запуске
with app.app_context():
    db.create_all()

# Главная страница - список клиентов
@app.route('/')
def index():
    return redirect(url_for('customers'))

# Список клиентов
@app.route('/customers')
def customers():
    search_query = request.args.get('search', '')
    search_by = request.args.get('search_by', 'all')
    
    if search_query:
        if search_by == 'all':
            customers = Customer.query.filter(
                (Customer.last_name.ilike(f'%{search_query}%')) |
                (Customer.first_name.ilike(f'%{search_query}%')) |
                (Customer.phone.ilike(f'%{search_query}%')) |
                (Customer.email.ilike(f'%{search_query}%'))
            ).order_by(Customer.last_name, Customer.first_name).all()
        elif search_by == 'date':
            customers = Customer.query.filter_by(registration_date=search_query)\
                .order_by(Customer.last_name, Customer.first_name).all()
        else:
            customers = Customer.query.order_by(Customer.last_name, Customer.first_name).all()
    else:
        customers = Customer.query.order_by(Customer.last_name, Customer.first_name).all()
    
    return render_template('customers.html', customers=customers, search_query=search_query, search_by=search_by)

# Форма добавления/редактирования клиента
@app.route('/customer/new', methods=['GET', 'POST'])
@app.route('/customer/edit/<int:customer_id>', methods=['GET', 'POST'])
def customer_form(customer_id=None):
    customer = None
    if customer_id:
        customer = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        try:
            if customer:
                # Редактирование существующего клиента
                customer.last_name = request.form['last_name']
                customer.first_name = request.form['first_name']
                customer.middle_name = request.form['middle_name'] or None
                customer.phone = request.form['phone']
                customer.email = request.form['email'] or None
                customer.registration_date = datetime.strptime(request.form['registration_date'], '%Y-%m-%d').date()
                customer.notes = request.form['notes'] or None
                flash('Данные клиента обновлены', 'success')
            else:
                # Создание нового клиента
                customer = Customer(
                    last_name=request.form['last_name'],
                    first_name=request.form['first_name'],
                    middle_name=request.form['middle_name'] or None,
                    phone=request.form['phone'],
                    email=request.form['email'] or None,
                    registration_date=datetime.strptime(request.form['registration_date'], '%Y-%m-%d').date(),
                    notes=request.form['notes'] or None
                )
                db.session.add(customer)
                flash('Клиент успешно добавлен', 'success')
            
            db.session.commit()
            return redirect(url_for('customers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка: {str(e)}', 'error')
    
    return render_template('customer_form.html', customer=customer)

# Удаление клиента
@app.route('/customer/delete/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()
        flash('Клиент удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')
    
    return redirect(url_for('customers'))

# Просмотр заказов клиента
@app.route('/customer/<int:customer_id>/orders')
def customer_orders(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', customer=customer, orders=orders, today=date.today())

# Добавление заказа
@app.route('/customer/<int:customer_id>/order/new', methods=['POST'])
def add_order(customer_id):
    try:
        order = Order(
            customer_id=customer_id,
            order_date=datetime.strptime(request.form['order_date'], '%Y-%m-%d').date(),
            product_name=request.form['product_name'],
            quantity=int(request.form['quantity']),
            price=float(request.form['price']),
            status=request.form['status'],
            notes=request.form['notes'] or None
        )
        db.session.add(order)
        db.session.commit()
        flash('Заказ добавлен', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка: {str(e)}', 'error')
    
    return redirect(url_for('customer_orders', customer_id=customer_id))

# Изменение статуса заказа
@app.route('/order/<int:order_id>/update_status', methods=['POST'])
def update_order_status(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        
        if new_status in ['active', 'completed', 'cancelled']:
            order.status = new_status
            db.session.commit()
            flash(f'Статус заказа обновлен на "{new_status}"', 'success')
        else:
            flash('Неверный статус', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка: {str(e)}', 'error')
    
    # Возвращаем на страницу заказов клиента
    return redirect(url_for('customer_orders', customer_id=order.customer_id))

# Удаление заказа
@app.route('/order/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        customer_id = order.customer_id
        db.session.delete(order)
        db.session.commit()
        flash('Заказ удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')
    
    return redirect(url_for('customer_orders', customer_id=customer_id))

# Отчеты - все заказы
@app.route('/reports')
def reports():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Фильтрация заказов по дате
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        orders = Order.query.filter(
            Order.order_date.between(start, end)
        ).order_by(Order.order_date.desc()).all()
    else:
        orders = Order.query.order_by(Order.order_date.desc()).all()
    
    # Расчет общей суммы
    total_amount = sum(order.total_price for order in orders)
    
    return render_template('reports.html', 
                         orders=orders,
                         total_amount=total_amount,
                         start_date=start_date,
                         end_date=end_date)

# API для получения статистики
@app.route('/api/statistics')
def get_statistics():
    total_customers = Customer.query.count()
    total_orders = Order.query.count()
    today = date.today()
    
    # Новые клиенты за сегодня
    new_customers_today = Customer.query.filter(
        Customer.registration_date == today
    ).count()
    
    # Заказы за сегодня
    orders_today = Order.query.filter(
        Order.order_date == today
    ).count()
    
    # Общая сумма заказов
    all_orders = Order.query.all()
    total_revenue = sum(order.total_price for order in all_orders)
    
    return jsonify({
        'total_customers': total_customers,
        'total_orders': total_orders,
        'new_customers_today': new_customers_today,
        'orders_today': orders_today,
        'total_revenue': total_revenue
    })

if __name__ == '__main__':
    app.run(debug=True)