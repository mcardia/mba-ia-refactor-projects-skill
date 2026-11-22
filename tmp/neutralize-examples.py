#!/usr/bin/env python3
"""Replace domain words inherited from the three sample projects with neutral ones in the skill references.

usage: neutralize-examples.py <references-dir>
"""
import pathlib
import re
import sys

# Ordered: longer / more specific keys first.
REPLACEMENTS = [
    ("SELECT c.id, c.title, u.name, p.amount, p.status FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id LEFT JOIN users u ON u.id = e.user_id LEFT JOIN payments p ON p.enrollment_id = e.id ORDER BY c.id, e.id",
     "SELECT i.id, i.title, u.name, y.amount, y.status FROM items i LEFT JOIN orders o ON o.item_id = i.id LEFT JOIN users u ON u.id = o.user_id LEFT JOIN payments y ON y.order_id = o.id ORDER BY i.id, o.id"),
    ("then group by course.", "then group by item."),
    ("get_todos_produtos", "get_all_items"),
    ("listar_produtos", "list_products"),
    ("checkoutController.handle", "purchaseController.handle"),
    ("checkoutService.checkout", "purchaseService.purchase"),
    ("{checkoutService,paymentGateway,reportService}", "{purchaseService,paymentGateway,reportService}"),
    ("{checkoutController,adminController,userController}", "{purchaseController,adminController,userController}"),
    ("{checkoutRoutes,adminRoutes,userRoutes}", "{purchaseRoutes,adminRoutes,userRoutes}"),
    ("{user,course,enrollment,payment}", "{user,item,order,payment}"),
    ("checkout logic, report logic, delete logic", "purchase logic, report logic, delete logic"),
    ("checkout orchestration", "purchase orchestration"),
    ("CheckoutService", "PurchaseService"),
    ("enrollmentModel", "orderModel"),
    ("courseModel", "itemModel"),
    ("sqlCourse", "sqlItem"),
    ("sqlEnroll", "sqlOrder"),
    ("findActive", "findAvailable"),
    ("courseId", "itemId"),
    ("course.price", "item.price"),
    ("course.id", "item.id"),
    ("'Course not found'", "'Item not found'"),
    ("const course =", "const item ="),
    ("!course", "!item"),
    ("const enrollment =", "const order ="),
    ("return enrollment;", "return order;"),
    ("enrollment.id", "order.id"),
    ("enrolls", "creates an order"),
    ("(err, course)", "(err, item)"),
    ("async function checkout(", "async function purchase("),
    ("checkout", "purchase"),
    ("AppManager", "GodManager"),
    ("badCrypto", "weakHash"),
    ("initDb", "initSchema"),
    ("setupRoutes", "registerRoutes"),
    ("logAndCache", "cacheValue"),
    ("globalCache", "sharedCache"),
    ("totalRevenue", "counter"),
    ("pedido_id", "order_id"),
    ("ENVIANDO EMAIL: pedido", "SENDING EMAIL: order"),
    ("faturamento", "revenue"),
    ("desconto", "discount"),
    ("Preço inválido", "Invalid price"),
    ("Erro interno do servidor", "Internal server error"),
    ('"erro"', '"error"'),
    ('"sucesso"', '"success"'),
    ('"dados"', '"data"'),
    ("len(user.tasks)", "len(user.orders)"),
    ("task.user.name", "order.user.name"),
    ("selectinload(Task.user), selectinload(Task.category)", "selectinload(Ticket.user), selectinload(Ticket.category)"),
    ("select(Task.status, func.count()).group_by(Task.status)", "select(Ticket.status, func.count()).group_by(Ticket.status)"),
    ("select(Task)", "select(Ticket)"),
    ("models/task.py", "models/ticket.py"),
    ("task_to_dict(task)", "ticket_to_dict(ticket)"),
    ("task.to_dict()", "ticket.to_dict()"),
    ("task.is_overdue()", "ticket.is_overdue()"),
    ("Task.query.get(task_id)", "Ticket.query.get(ticket_id)"),
    ("db.session.get(Task, task_id)", "db.session.get(Ticket, ticket_id)"),
    ("task = ", "ticket = "),
    ("`u, e, p, cc, cid` -> `name, email, password, cardNumber, itemId`", "`u, e, p, cc, pid` -> `name, email, password, cardNumber, productId`"),
    ("`cc`, `cid`", "`cc`, `pid`"),
]


def main():
    directory = pathlib.Path(sys.argv[1])
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"updated {path.name}")


if __name__ == "__main__":
    main()
