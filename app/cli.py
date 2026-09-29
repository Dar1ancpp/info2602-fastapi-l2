import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from sqlmodel import select, or_
from sqlalchemy.exc import IntegrityError

cli = typer.Typer(help="CLI tool for managing database users.")

@cli.command()
def initialize():
    """
    Initialize the database by dropping existing tables, creating fresh tables, and adding initial data.
    """
    with get_session() as db:  # Get a connection to the database
        drop_all()  # delete all tables
        create_db_and_tables()  # recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass')  # Create a new user (in memory)
        db.add(bob)  # Tell the database about this new data
        db.commit()  # Tell the database to persist the data
        db.refresh(bob)  # Update the user (to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(
    username: str = typer.Argument(..., help="The exact username of the user to retrieve.")
):
    """
    Retrieve and print a user by their username.
    """
    with get_session() as db:  # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """
    Retrieve and display all users currently stored in the database.
    """
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)

@cli.command()
def change_email(
    username: str = typer.Argument(..., help="The username of the user whose email will be updated."),
    new_email: str = typer.Argument(..., help="The new email address to set.")
):
    """
    Update the email address of a user identified by their username.
    """
    with get_session() as db:  # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: str = typer.Argument(..., help="The username for the new user."),
    email: str = typer.Argument(..., help="The email address for the new user."),
    password: str = typer.Argument(..., help="The password for the new user.")
):
    """
    Create a new user with unique username and email constraints handled.
    """
    with get_session() as db:  # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback()  # undo any previous steps of a transaction
            print("Username or email already taken!")  # user friendly message
        else:
            print(newuser)  # print the newly created user

@cli.command()
def delete_user(
    username: str = typer.Argument(..., help="The username of the user to delete.")
):
    """
    Delete a user from the database by their username.
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

@cli.command()
def search_users(
    query: str = typer.Argument(..., help="Partial string to search within usernames or emails.")
):
    """
    Find users matching a partial string in their username OR email address (Exercise 1).
    """
    with get_session() as db:
        users = db.exec(
            select(User).where(
                or_(
                    User.username.contains(query),
                    User.email.contains(query)
                )
            )
        ).all()
        if not users:
            print(f"No users matching '{query}' found!")
        else:
            for user in users:
                print(user)

@cli.command()
def list_users(
    limit: int = typer.Option(10, help="Maximum number of users to return."),
    offset: int = typer.Option(0, help="Number of users to skip before returning results.")
):
    """
    List users using limit and offset parameters for paginated queries (Exercise 2).
    """
    with get_session() as db:
        users = db.exec(select(User).offset(offset).limit(limit)).all()
        if not users:
            print("No users found.")
        else:
            for user in users:
                print(user)

if __name__ == "__main__":
    cli()