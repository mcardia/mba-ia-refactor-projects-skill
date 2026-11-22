"""Script para popular o banco com dados iniciais"""
import logging
from datetime import timedelta

from app import app
from config.constants import (ROLE_ADMIN, ROLE_MANAGER, ROLE_USER, STATUS_CANCELLED, STATUS_DONE,
                              STATUS_IN_PROGRESS, STATUS_PENDING)
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.time import utc_now

logger = logging.getLogger('seed')

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
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = []
        for name, email, password, role in USERS:
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            users.append(user)
        db.session.commit()
        joao, maria, pedro = users

        categories = [Category(name=name, description=description, color=color)
                      for name, description, color in CATEGORIES]
        db.session.add_all(categories)
        db.session.commit()
        backend, frontend, devops, bug = categories

        now = utc_now()
        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': STATUS_PENDING, 'priority': 1, 'user': joao, 'category': backend, 'due_date': now - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': STATUS_IN_PROGRESS, 'priority': 2, 'user': maria, 'category': frontend, 'due_date': now + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': STATUS_DONE, 'priority': 2, 'user': pedro, 'category': devops, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': STATUS_PENDING, 'priority': 1, 'user': joao, 'category': bug, 'due_date': now - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': STATUS_PENDING, 'priority': 3, 'user': joao, 'category': backend, 'due_date': now + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': STATUS_PENDING, 'priority': 2, 'user': maria, 'category': backend},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': STATUS_CANCELLED, 'priority': 4, 'user': pedro, 'category': backend},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': STATUS_IN_PROGRESS, 'priority': 3, 'user': maria, 'category': backend, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': STATUS_PENDING, 'priority': 4, 'user': pedro, 'category': devops, 'due_date': now + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': STATUS_PENDING, 'priority': 3, 'user': joao, 'category': backend, 'tags': 'improvement,validation'},
        ]
        for task_data in tasks_data:
            db.session.add(Task(
                title=task_data['title'],
                description=task_data['description'],
                status=task_data['status'],
                priority=task_data['priority'],
                user_id=task_data['user'].id,
                category_id=task_data['category'].id,
                due_date=task_data.get('due_date'),
                tags=task_data.get('tags'),
            ))
        db.session.commit()

        logger.info('Seed concluído com sucesso!')
        logger.info('  %s usuários', User.count_all())
        logger.info('  %s categorias', Category.count_all())
        logger.info('  %s tasks', Task.count_all())


if __name__ == '__main__':
    seed_data()
