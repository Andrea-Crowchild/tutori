#!/usr/bin/env python3
# TODO: Add headers to list all and stats list all
# TODO: Add types to all command
# TODO: Add more error checking
# TODO: Change "entry" or "item" to "card"
import json
import os
from datetime import date, datetime, timedelta, timezone

import click
from fsrs import ReviewLog, Scheduler

from tutoricard import TutoriCard, backup_data, load_data, save_data

CONFIG_FILE = os.path.expanduser("~/.config/tutori/tutori.json")


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """View due items"""
    # TODO: Improve docstrings

    if ctx.invoked_subcommand is not None:
        return

    cards, scheduler = load_data()

    #  checks if cards is 0 or None
    if not cards:
        return

    now = datetime.now(timezone.utc)
    width = max(len(name) for name in cards) + 2
    cards = dict(sorted(cards.items(), key=lambda x: x[1].card.due))

    for card in cards.values():
        if card.card.due <= now:
            print(f"{card.nametag.ljust(width)}", ":", f"{card.description}")


@cli.command()
def all():
    """View all items stored by Tutori"""
    # TODO: Develop headers
    # TODO: Improve docstrings

    cards, scheduler = load_data()
    # checks if cards is 0 as well as None

    if not cards:
        return

    name_width = max(len(name) for name in cards) + 2
    date_width = max(len(str(card.card.due.date())) for card in cards.values())
    cards = dict(sorted(cards.items()))

    for card in cards.values():
        print(
            f"{card.nametag.ljust(name_width)}",
            ":",
            f"{card.card.due.strftime('%Y-%m-%d %H:%M').ljust(date_width)}",
            ":",
            f"{card.description}",
        )


@cli.command()
def all_stats():
    """View all items stored by Tutori"""
    # TODO: Develop headers
    # TODO: Improve docstrings

    cards, scheduler = load_data()
    # checks if cards is 0 as well as None

    if not cards:
        return
    if scheduler is None:
        return

    name_width = max(len(name) for name in cards) + 2
    date_width = max(len(str(card.card.due.date())) for card in cards.values())
    cards = dict(sorted(cards.items()))

    for card in cards.values():
        reps = len(card.review_logs)
        difficulty = card.card.difficulty
        retrievability = scheduler.get_card_retrievability(card.card)
        stability = card.card.stability

        print(
            f"{card.nametag.ljust(name_width)}",
            ":",
            f"{card.card.due.strftime('%Y-%m-%d %H:%M').ljust(date_width)}",
            ":",
            f"Reps {reps}",
            ":",
            f"Ret. {retrievability:.3f}",
            ":",
            f"Sta. {stability:.3f}",
            ":",
            f"Diff. {difficulty:.2f}",
            ":",
            f"{card.description}",
        )


# TODO: Add docstrings
@cli.command()
@click.argument("days_in", default=3, required=False, type=int)
def upcoming(days_in):
    """Displays all cards due in N number of days, if no argument is provided,
    default is 3"""

    cards, scheduler = load_data()

    # checks if cards is zero or None
    if not cards:
        return

    days_from_today = date.today() + timedelta(days=days_in)
    cards = dict(sorted(cards.items(), key=lambda x: x[1].card.due))
    name_width = max(len(name) for name in cards) + 2
    date_width = max(len(str(card.card.due.date())) for card in cards.values())

    for card in cards.values():
        if card.card.due.date() <= days_from_today:
            print(
                f"{card.nametag.ljust(name_width)}",
                ":",
                f"{str(card.card.due.strftime('%Y-%m-%d %H:%M')).ljust(date_width)}",
                ":",
                f"{card.description}",
            )


@cli.command()
@click.argument("nametag", type=str)
def show(nametag):
    """Displays the answer of an entry"""

    cards, scheduler = load_data()

    if cards is None:
        return
    if nametag not in cards:
        print("That's not an entry")
        return

    print(f"Answer: {cards[nametag].answer}")


@cli.command()
def new():
    """Initialize or clear your save file"""
    # TODO: Improve docstrings

    if os.path.exists(CONFIG_FILE):
        cards, scheduler = load_data()

        print("Are you sure you want to delete your file and start over?")
        print("Y/N to continue")
        choice = input()

        if choice == "Y" or choice == "y":
            cards = {}
            save_data(cards, scheduler)
            return
        else:
            return

    config_dir = os.path.expanduser("~/.config/tutori/")
    os.makedirs(config_dir, exist_ok=True)

    cards = {}
    scheduler = Scheduler()
    save_data(cards, scheduler)


@cli.command()
def reset():
    """Reset scheduler optimization"""
    # TODO: Improve docstrings

    if os.path.exists(CONFIG_FILE):
        cards, scheduler = load_data()
        print("Reset scheduler optimization?")
        print("Y/N to continue")
        choice = input()
        if choice == "Y" or choice == "y":
            scheduler = Scheduler()
            save_data(cards, scheduler)
            return
        else:
            return

    config_dir = os.path.expanduser("~/.config/tutori/")
    os.makedirs(config_dir, exist_ok=True)

    cards = {}
    scheduler = Scheduler()
    save_data(cards, scheduler)


@cli.command()
@click.argument("nametag", type=str)
@click.argument("description", type=str)
@click.argument("answer", required=False, type=str)
def add(nametag, description, answer):
    """Add an entry to Tutori"""
    # TODO: Improve docstrings

    cards, scheduler = load_data()
    if cards is None:
        return

    if nametag in cards:
        print("That's already an entry")
        return

    if len(nametag) > 7:
        print("Nametag is too long, use 7 characters or fewer")
        return

    cards[nametag] = TutoriCard(nametag, description, answer or "")
    # cards[nametag].card.due = datetime.now(timezone.utc) + timedelta(days=1)

    save_data(cards, scheduler)


@cli.command(name="rate")
@click.argument("nametag", type=str)
@click.argument("rating", type=int)
def rate(nametag, rating):
    """Rate an entry on a scale of 1 to 4"""
    # TODO: Improve docstrings
    cards, scheduler = load_data()
    if cards is None:
        return
    if scheduler is None:
        return
    if nametag not in cards:
        print("That's not a card")
        return
    if rating > 4 or rating < 1:
        print("Rating must be an integer between 1 and 4")
        return

    cards[nametag].card, review_log = scheduler.review_card(cards[nametag].card, rating)

    due_date = cards[nametag].card.due.strftime("%Y-%m-%d %H:%M")
    review_time = review_log.review_datetime.strftime("%Y-%m-%d %H:%M")
    cards[nametag].review_logs.append(json.loads(review_log.to_json()))

    if cards[nametag].answer != "":
        print(f"Answer: {cards[nametag].answer}")
    print(f"Card rated {review_log.rating} on {review_time}")
    print(f"Card next due on {due_date}")

    now = datetime.now(timezone.utc)
    due_cards = []
    for card in cards.values():
        if card.card.due <= now:
            due_cards.append(card)
    if len(due_cards) > 0:
        next_card = due_cards[0]
        print(f"Next card is: {next_card.nametag}")
        print(next_card.description)

    save_data(cards, scheduler)


@cli.command()
@click.argument("old_name", type=str)
@click.argument("new_name", type=str)
@click.argument("description", required=False, type=str)
@click.argument("answer", required=False, type=str)
def edit(old_name, new_name, description, answer):
    """Change a card's information"""
    # TODO: Improve docstrings

    cards, scheduler = load_data()

    if cards is None:
        return
    if old_name not in cards:
        print("That's not an entry")
        return
    if len(new_name) > 7:
        print("Nametag is too long, use 7 characters or fewer")
        return

    if old_name == new_name:
        if description is not None:
            cards[new_name].description = description
        if answer is not None:
            cards[new_name].answer = answer
    else:
        if new_name in cards:
            print("That's already an entry")
            return

        temp = cards[old_name]
        cards.pop(old_name)
        cards[new_name] = temp
        cards[new_name].nametag = new_name

        if description is not None:
            cards[new_name].description = description
        if answer is not None:
            cards[new_name].answer = answer

    save_data(cards, scheduler)


@cli.command()
@click.argument("nametag", type=str)
def remove(nametag):
    """Remove an entry from Tutori"""
    # TODO: Improve docstrings

    cards, scheduler = load_data()

    if cards is None:
        return
    if nametag not in cards:
        print("That's not an entry")
        return

    cards.pop(nametag)

    save_data(cards, scheduler)


# TODO: Improve docstrings
@cli.command()
def clean():
    """Remove entries scheduled further out than one year"""

    cards, scheduler = load_data()

    if cards is None:
        return

    print("Clean entries?")
    print("Press Y/N to continue")
    choice = input()

    if choice != "Y" and choice != "y":
        return
    if len(cards) == 0:
        return

    one_year_out = date.today() + timedelta(days=365)
    entries_to_clean = []

    for name, card in cards.items():
        if card.card.due.date() > one_year_out:
            entries_to_clean.append(name)

    for name in entries_to_clean:
        cards.pop(name)

    save_data(cards, scheduler)


@cli.command()
@click.argument("location", type=str)
def save(location):
    """Save a backup of your file, input path as string"""
    # TODO: Improve docstrings
    cards, scheduler = load_data()

    backup_data(cards, scheduler, location)


@cli.command()
def optimize():
    """Run the optimizer on your saved data to custom tune scheduler parameters
    to you"""
    # TODO: Improve docstrings

    from fsrs import Optimizer

    cards, scheduler = load_data()
    # checks to see if cards is empty or 0 prior ot running

    if not cards:
        return

    all_logs = []

    for card in cards.values():
        for log in card.review_logs:
            all_logs.append(ReviewLog.from_json(json.dumps(log)))

    optimizer = Optimizer(all_logs)
    optimal_parameters = optimizer.compute_optimal_parameters()
    optimal_scheduler = Scheduler(optimal_parameters)

    print(optimal_parameters)

    for card in cards.values():
        card.card = optimal_scheduler.reschedule_card(
            card.card,
            [ReviewLog.from_json(json.dumps(log)) for log in card.review_logs],
        )

    save_data(cards, optimal_scheduler)


@cli.command()
def scheduler():
    """Print current scheduler parameters"""
    # TODO: Improve docstrings

    cards, scheduler = load_data()

    if scheduler is None:
        return
    print(scheduler.parameters)


@cli.command()
@click.argument("nametag", type=str)
def stats(nametag):
    """Get the retrievability stat of a card"""
    # TODO: Improve docstrings

    cards, scheduler = load_data()

    if scheduler is None:
        return
    if cards is None:
        return
    if nametag not in cards:
        print("That's not an entry")
        return

    reps = len(cards[nametag].review_logs)
    difficulty = cards[nametag].card.difficulty
    retrievability = scheduler.get_card_retrievability(cards[nametag].card)
    stability = cards[nametag].card.stability

    print(f"Times trained: {reps}")
    print(f"Card retrievability: {retrievability}")
    print(f"Card stability: {stability}")
    print(f"Card difficulty: {difficulty}")


cli.add_command(add, name="a")
cli.add_command(all, name="la")
cli.add_command(all_stats, name="las")
cli.add_command(edit, name="e")
cli.add_command(rate, name="r")
cli.add_command(remove, name="rm")
cli.add_command(stats, name="st")
cli.add_command(show, name="s")
cli.add_command(upcoming, name="u")


if __name__ == "__main__":
    cli()
