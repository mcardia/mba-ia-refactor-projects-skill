"""Script para popular o banco com dados iniciais"""
from datetime import timedelta

from sqlalchemy import delete

from app import app, db
from config.constants import (ROLE_ADMIN, ROLE_MANAGER, ROLE_USER, STATUS_CANCELLED, STATUS_DONE,
                              STATUS_IN_PROGRESS, STATUS_PENDING)
from models import Category, Task, User
from utils.time import utc_now

USERS = [
    ('João Silva', 'joao@email.com', '1234', ROLE_ADMIN),
    ('Maria Santos', 'maria@email.com', 'abcd', ROLE_USER),
    ('Pedro Oliveira', 'pedro@email.com', 'pass', ROLE_MANAGER),
]

CATEGORIES = [
    ('Backend', 'Tarefas de backend', '#3498db'),
    ('Frontend', 'Tarefas de frontend', '#2ecc71'),
    ('DevOps', 'Tarefas de infraestrutura', '#e74c3c'),
    ('Bug', 'Correção de bugs', '#e67e22'),
]


def seed_data():
    with app.app_context():
        for model in (Task, User, Category):
            db.session.execute(delete(model))
        db.session.commit()

        users = []
        for name, email, password, role in USERS:
            user = User(name=name, email=email, role=role)
            user.set_password(password)  # salted hash; the plaintext stays usable for login
            users.append(user)
        db.session.add_all(users)
        joao, maria, pedro = users

        backend, frontend, devops, bug = categories = [
            Category(name=name, description=description, color=color) for name, description, color in CATEGORIES
        ]
        db.session.add_all(categories)
        db.session.commit()

        now = utc_now()
        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': STATUS_PENDING, 'priority': 1, 'user_id': joao.id, 'category_id': backend.id, 'due_date': now - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': STATUS_IN_PROGRESS, 'priority': 2, 'user_id': maria.id, 'category_id': frontend.id, 'due_date': now + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': STATUS_DONE, 'priority': 2, 'user_id': pedro.id, 'category_id': devops.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': STATUS_PENDING, 'priority': 1, 'user_id': joao.id, 'category_id': bug.id, 'due_date': now - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': STATUS_PENDING, 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'due_date': now + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': STATUS_PENDING, 'priority': 2, 'user_id': maria.id, 'category_id': backend.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': STATUS_CANCELLED, 'priority': 4, 'user_id': pedro.id, 'category_id': backend.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': STATUS_IN_PROGRESS, 'priority': 3, 'user_id': maria.id, 'category_id': backend.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': STATUS_PENDING, 'priority': 4, 'user_id': pedro.id, 'category_id': devops.id, 'due_date': now + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': STATUS_PENDING, 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'tags': 'improvement,validation'},
        ]
        db.session.add_all(Task(**task_data) for task_data in tasks_data)
        db.session.commit()

        # CLI output of the seed script (not application logging)
        print("Seed concluído com sucesso!")
        print(f"  {User.count()} usuários")
        print(f"  {Category.count()} categorias")
        print(f"  {Task.count()} tasks")


if __name__ == '__main__':
    seed_data()
