from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from database import db, init_db
from models import Customer, Order
import sqlite3
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
init_db(app)

def create_sample_data():
    """Создание тестовых данных"""
    # Проверяем, есть ли уже клиенты в базе
    if Customer.query.count() > 0:
        return
    
    # Список тестовых клиентов
    sample_customers = [
        # Фамилия, Имя, Отчество, Email, Телефон, Дата регистрации, Примечания
        ('Иванов', 'Александр', 'Петрович', 'ivanov@mail.ru', '+79161234567', '2024-01-15', 'Постоянный клиент'),
        ('Петрова', 'Мария', 'Сергеевна', 'petrova@gmail.com', '+79162345678', '2024-01-20', 'Корпоративный клиент'),
        ('Сидоров', 'Дмитрий', 'Игоревич', 'sidorov@yandex.ru', '+79163456789', '2024-02-05', 'Новый клиент'),
        ('Кузнецова', 'Ольга', 'Владимировна', 'kuznetsova@mail.ru', '+79164567890', '2024-02-10', 'VIP клиент'),
        ('Попов', 'Сергей', 'Александрович', 'popov@gmail.com', '+79165678901', '2024-02-15', 'Частый заказчик'),
        ('Васильева', 'Елена', 'Дмитриевна', 'vasileva@yandex.ru', '+79166789012', '2024-02-20', 'Оптовый покупатель'),
        ('Смирнов', 'Андрей', 'Викторович', 'smirnov@mail.ru', '+79167890123', '2024-03-01', 'Мелкий опт'),
        ('Федорова', 'Наталья', 'Павловна', 'fedorova@gmail.com', '+79168901234', '2024-03-05', 'Розничный клиент'),
        ('Морозов', 'Иван', 'Сергеевич', 'morozov@yandex.ru', '+79169012345', '2024-03-10', 'Новый'),
        ('Новикова', 'Татьяна', 'Ивановна', 'novikova@mail.ru', '+79160123456', '2024-03-15', 'По рекомендации'),
        ('Волков', 'Павел', 'Олегович', 'volkov@gmail.com', '+79161234567', '2024-03-20', 'Корпоративный'),
        ('Алексеева', 'Светлана', 'Михайловна', 'alekseeva@yandex.ru', '+79162345678', '2024-03-25', 'Постоянный'),
        ('Лебедев', 'Максим', 'Андреевич', 'lebedev@mail.ru', '+79163456789', '2024-04-01', 'VIP'),
        ('Козлова', 'Анна', 'Витальевна', 'kozlova@gmail.com', '+79164567890', '2024-04-05', 'Частый'),
        ('Семенов', 'Виктор', 'Николаевич', 'semenov@yandex.ru', '+79165678901', '2024-04-10', 'Оптовый')
    ]
    
    # Список тестовых товаров для заказов
    sample_products = [
        ('Ноутбук Lenovo', 1, 45000.00),
        ('Мышь компьютерная', 2, 1500.00),
        ('Клавиатура механическая', 1, 3500.00),
        ('Монитор 24"', 1, 18000.00),
        ('Наушники беспроводные', 1, 7000.00),
        ('Смартфон Samsung', 1, 35000.00),
        ('Планшет Apple', 1, 45000.00),
        ('Принтер лазерный', 1, 12000.00),
        ('Веб-камера', 1, 3000.00),
        ('Флеш-накопитель 64GB', 3, 2500.00),
        ('Внешний жесткий диск 1TB', 1, 5000.00),
        ('Колонки Bluetooth', 1, 6000.00),
        ('Роутер Wi-Fi', 1, 4000.00),
        ('Игровая консоль', 1, 30000.00),
        ('Умные часы', 1, 8000.00)
    ]
    
    # Статусы заказов
    order_statuses = ['Новый', 'В обработке', 'Выполнен', 'Отменен']
    
    try:
        # Добавляем клиентов
        customers = []
        for customer_data in sample_customers:
            customer = Customer(
                last_name=customer_data[0],
                first_name=customer_data[1],
                middle_name=customer_data[2],
                email=customer_data[3],
                phone=customer_data[4],
                registration_date=datetime.strptime(customer_data[5], '%Y-%m-%d').date(),
                notes=customer_data[6]
            )
            db.session.add(customer)
            customers.append(customer)
        
        db.session.commit()
        
        # Добавляем заказы для клиентов
        for i, customer in enumerate(customers):
            # Каждый клиент получает 1-3 заказа
            num_orders = random.randint(1, 3)
            for j in range(num_orders):
                product = random.choice(sample_products)
                order_date = customer.registration_date + timedelta(days=random.randint(1, 30))
                
                order = Order(
                    customer_id=customer.id,
                    order_date=order_date,
                    product_name=product[0],
                    quantity=product[1],
                    price=product[2],
                    status=random.choice(order_statuses),
                    notes=f'Заказ №{j+1} для {customer.first_name} {customer.last_name}'
                )
                db.session.add(order)
        
        db.session.commit()
        print("✅ Тестовые данные успешно созданы!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка при создании тестовых данных: {e}")

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

# Обновление статуса заказа
@app.route('/order/<int:order_id>/update_status', methods=['POST'])
def update_order_status(order_id):
    """Обновление статуса заказа"""
    try:
        new_status = request.form['status']
        
        # Проверяем допустимые статусы
        allowed_statuses = ['Новый', 'В обработке', 'Выполнен', 'Отменен']
        if new_status not in allowed_statuses:
            flash('Недопустимый статус заказа', 'error')
            return redirect(request.referrer or url_for('index'))
        
        # Находим заказ и обновляем статус
        order = Order.query.get_or_404(order_id)
        order.status = new_status
        db.session.commit()
        
        flash(f'Статус заказа обновлен на: {new_status}', 'success')
        
        # Возвращаем обратно к заказам клиента
        return redirect(url_for('customer_orders', customer_id=order.customer_id))
            
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении статуса: {str(e)}', 'error')
        return redirect(request.referrer or url_for('index'))

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
    # Создаем тестовые данные в контексте приложения
    with app.app_context():
        create_sample_data()
    app.run(debug=True)