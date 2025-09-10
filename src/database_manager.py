
#!/usr/bin/env python3
import os
import sys
from app import app, db

def show_current_database():
    """Mostra qual banco está sendo usado atualmente"""
    with app.app_context():
        engine = db.engine
        url = str(engine.url)
        
        if url.startswith("sqlite"):
            print("📊 Banco atual: SQLite (Desenvolvimento)")
            print(f"   Arquivo: {url.replace('sqlite:///', '')}")
        elif url.startswith("postgresql"):
            print("📊 Banco atual: PostgreSQL (Produção)")
            print(f"   URL: {url}")
        else:
            print(f"📊 Banco atual: {url}")

def create_tables():
    """Cria todas as tabelas no banco atual"""
    with app.app_context():
        db.create_all()
        print("✅ Tabelas criadas no banco atual")

def show_stats():
    """Mostra estatísticas do banco atual"""
    from models import User, Product, Allocation, StockMovement
    
    with app.app_context():
        try:
            users_count = User.query.count()
            products_count = Product.query.count()
            allocations_count = Allocation.query.count()
            movements_count = StockMovement.query.count()
            
            print("📈 Estatísticas do banco:")
            print(f"   - Usuários: {users_count}")
            print(f"   - Produtos: {products_count}")
            print(f"   - Alocações: {allocations_count}")
            print(f"   - Movimentações: {movements_count}")
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")

def main():
    if len(sys.argv) < 2:
        print("🔧 Gerenciador de Banco de Dados")
        print("\nComandos disponíveis:")
        print("  status     - Mostra qual banco está sendo usado")
        print("  create     - Cria todas as tabelas")
        print("  stats      - Mostra estatísticas do banco")
        print("  migrate-to-sqlite    - Migra PostgreSQL → SQLite")
        print("  migrate-to-postgres  - Migra SQLite → PostgreSQL")
        print("\nExemplo: python database_manager.py status")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_current_database()
    elif command == "create":
        create_tables()
    elif command == "stats":
        show_stats()
    elif command == "migrate-to-sqlite":
        from migrate_to_sqlite import migrate_postgres_to_sqlite
        migrate_postgres_to_sqlite()
    elif command == "migrate-to-postgres":
        from migrate_to_postgres import migrate_sqlite_to_postgres
        migrate_sqlite_to_postgres()
    else:
        print(f"❌ Comando desconhecido: {command}")

if __name__ == "__main__":
    main()
