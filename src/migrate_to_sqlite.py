
import os
import sqlite3
from app import app, db
from models import User, Product, Allocation, StockMovement
from sqlalchemy import create_engine, text
from datetime import datetime

def migrate_postgres_to_sqlite():
    """Migra dados do PostgreSQL para SQLite"""
    
    # Conectar ao PostgreSQL (produção)
    postgres_url = os.environ.get("DATABASE_URL")
    if not postgres_url or not postgres_url.startswith("postgres"):
        print("❌ Variável DATABASE_URL do PostgreSQL não encontrada!")
        print("Configure a variável de ambiente DATABASE_URL com a URL do PostgreSQL.")
        return
    
    print("🔄 Iniciando migração do PostgreSQL para SQLite...")
    
    try:
        # Engine do PostgreSQL
        postgres_engine = create_engine(postgres_url)
        
        with app.app_context():
            # Remover o banco SQLite existente
            if os.path.exists("inventory.db"):
                os.remove("inventory.db")
                print("🗑️  Banco SQLite anterior removido")
            
            # Criar tabelas no SQLite
            db.create_all()
            print("✅ Tabelas SQLite criadas")
            
            # Migrar usuários
            with postgres_engine.connect() as pg_conn:
                users_result = pg_conn.execute(text("SELECT * FROM users ORDER BY id"))
                users_data = users_result.fetchall()
                
                for user_row in users_data:
                    user = User(
                        id=user_row.id,
                        username=user_row.username,
                        email=user_row.email,
                        password_hash=user_row.password_hash,
                        role=user_row.role,
                        is_admin=user_row.is_admin,
                        is_active=user_row.is_active,
                        created_at=user_row.created_at,
                        created_by=user_row.created_by,
                        reset_token=user_row.reset_token,
                        reset_token_expires=user_row.reset_token_expires
                    )
                    db.session.merge(user)
                
                db.session.commit()
                print(f"✅ {len(users_data)} usuários migrados")
            
            # Migrar produtos
            with postgres_engine.connect() as pg_conn:
                products_result = pg_conn.execute(text("SELECT * FROM products ORDER BY id"))
                products_data = products_result.fetchall()
                
                for product_row in products_data:
                    product = Product(
                        id=product_row.id,
                        code=product_row.code,
                        name=product_row.name,
                        supplier_reference=product_row.supplier_reference,
                        location=product_row.location,
                        quantity=product_row.quantity,
                        unit=product_row.unit,
                        photo_filename=product_row.photo_filename,
                        supplier_name=product_row.supplier_name,
                        created_at=product_row.created_at,
                        updated_at=product_row.updated_at,
                        created_by=product_row.created_by
                    )
                    db.session.merge(product)
                
                db.session.commit()
                print(f"✅ {len(products_data)} produtos migrados")
            
            # Migrar alocações
            with postgres_engine.connect() as pg_conn:
                allocations_result = pg_conn.execute(text("SELECT * FROM allocations ORDER BY id"))
                allocations_data = allocations_result.fetchall()
                
                for allocation_row in allocations_data:
                    allocation = Allocation(
                        id=allocation_row.id,
                        product_id=allocation_row.product_id,
                        user_id=allocation_row.user_id,
                        work_number=allocation_row.work_number,
                        quantity=allocation_row.quantity,
                        allocated_at=allocation_row.allocated_at,
                        notes=allocation_row.notes,
                        status=allocation_row.status,
                        approved_by_id=allocation_row.approved_by_id,
                        approved_at=allocation_row.approved_at,
                        approval_notes=allocation_row.approval_notes
                    )
                    db.session.merge(allocation)
                
                db.session.commit()
                print(f"✅ {len(allocations_data)} alocações migradas")
            
            # Migrar movimentações de estoque
            with postgres_engine.connect() as pg_conn:
                movements_result = pg_conn.execute(text("SELECT * FROM stock_movements ORDER BY id"))
                movements_data = movements_result.fetchall()
                
                for movement_row in movements_data:
                    movement = StockMovement(
                        id=movement_row.id,
                        product_id=movement_row.product_id,
                        user_id=movement_row.user_id,
                        movement_type=movement_row.movement_type,
                        quantity=movement_row.quantity,
                        previous_quantity=movement_row.previous_quantity,
                        new_quantity=movement_row.new_quantity,
                        notes=movement_row.notes,
                        created_at=movement_row.created_at
                    )
                    db.session.merge(movement)
                
                db.session.commit()
                print(f"✅ {len(movements_data)} movimentações de estoque migradas")
            
            print("🎉 Migração concluída com sucesso!")
            print("💡 Agora o projeto usará SQLite localmente e PostgreSQL em produção.")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        raise e

if __name__ == "__main__":
    migrate_postgres_to_sqlite()
