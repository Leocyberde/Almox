
import os
from app import app, db
from models import User, Product, Allocation, StockMovement
from sqlalchemy import create_engine, text

def migrate_sqlite_to_postgres():
    """Migra dados do SQLite para PostgreSQL"""
    
    postgres_url = os.environ.get("DATABASE_URL")
    if not postgres_url or not postgres_url.startswith("postgres"):
        print("❌ Variável DATABASE_URL do PostgreSQL não encontrada!")
        return
    
    if not os.path.exists("inventory.db"):
        print("❌ Banco SQLite não encontrado!")
        return
    
    print("🔄 Iniciando migração do SQLite para PostgreSQL...")
    
    try:
        # Temporariamente usar SQLite
        temp_app = app
        temp_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
        
        with temp_app.app_context():
            # Ler dados do SQLite
            users = User.query.all()
            products = Product.query.all()
            allocations = Allocation.query.all()
            movements = StockMovement.query.all()
            
            print(f"📊 Dados encontrados no SQLite:")
            print(f"   - {len(users)} usuários")
            print(f"   - {len(products)} produtos")
            print(f"   - {len(allocations)} alocações")
            print(f"   - {len(movements)} movimentações")
        
        # Conectar ao PostgreSQL
        postgres_engine = create_engine(postgres_url)
        temp_app.config["SQLALCHEMY_DATABASE_URI"] = postgres_url
        
        with temp_app.app_context():
            # Recriar tabelas no PostgreSQL
            db.create_all()
            print("✅ Tabelas PostgreSQL criadas/atualizadas")
            
            # Migrar dados
            for user in users:
                db.session.merge(user)
            db.session.commit()
            print(f"✅ {len(users)} usuários migrados")
            
            for product in products:
                db.session.merge(product)
            db.session.commit()
            print(f"✅ {len(products)} produtos migrados")
            
            for allocation in allocations:
                db.session.merge(allocation)
            db.session.commit()
            print(f"✅ {len(allocations)} alocações migradas")
            
            for movement in movements:
                db.session.merge(movement)
            db.session.commit()
            print(f"✅ {len(movements)} movimentações migradas")
            
            print("🎉 Migração para PostgreSQL concluída!")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        raise e

if __name__ == "__main__":
    migrate_sqlite_to_postgres()
