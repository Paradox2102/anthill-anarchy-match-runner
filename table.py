#!/usr/bin/env python3

# This module provides the methods that build complex HTML fragments.

import config
import sheet
import overlay

def show_matches():
    """ Build and show the table for all qualifying matches """
    # Only show qualifying rounds, not final playoffs.
    n_qualifying_rounds = 10 # TODO: Don't hard-code this!
    matches = sheet.get_matches(flush=True)[:n_qualifying_rounds]
    text = config.env.get_template('match.html').render(matches=matches)
    config.logger.info(f"Match table: {text}")
    overlay.show_table("Matches", text)

    
def show_teams():
    """ Build and show the table for all teams """
    teams = sheet.get_teams(flush=True)
    teams = sorted(teams, key=lambda t: (t['Rank'], t['Team']))
    config.logger.info(f"Sorted teams: {teams}")
    text = config.env.get_template('team.html').render(teams=teams)
    config.logger.info(f"Team table: {text}")
    overlay.show_table("Teams", text)

    
def show_match(match_id):
    """ Build and show the detailed results table for one match """
    match = sheet.get_match(match_id, flush=True)
    text = config.env.get_template('match_score.html').render(match=match)
    config.logger.info(f"Match score table: {text}")
    overlay.show_table("Match", text)