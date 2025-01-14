import os
import threading
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import xlsxwriter
from datetime import datetime
import pytz
import logging
import yaml
from flask import Flask, send_file, request, Response


MONTH_INT = int(datetime.strftime(datetime.today(), '%m'))
YEAR_INT = int(datetime.strftime(datetime.today(), '%Y'))
if MONTH_INT >= 10:
    YEAR_INT += 1

SELECT_MODE = False
SELECT_TEAMS = []
MEN_URL = f'http://warrennolan.com/basketball/{str(YEAR_INT)}/net-nitty'
TEAM_URL_TEMPLATE = f'http://warrennolan.com/basketball/{str(YEAR_INT)}/team-net-sheet?team='
LOG_FNAME = 'warrennolan_log.txt'
COL_LETTER_MAP = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
COL_SETTINGS = {
    'NET': {
        'keymap': 'net',
        'width': 5
    },
    'Team': {
        'keymap': 'team',
        'width': 19,
        'left_align': True
    },
    'Team Link': {
        'keymap': 'team_url',
        'width': 19,
        'left_align': True
    },
    'Record': {
        'keymap': 'overall_record',
        'width': 7,
        'two_digit_text_year': True
    },
    'Conf Record': {
        'keymap': 'conf_record',
        'width': 11,
        'two_digit_text_year': True
    },
    'Road/Neutral Record': {
        'keymap': 'combined_road_neutral_record',
        'width': 19,
        'two_digit_text_year': True
    },
    'Q3/Q4 Losses': {
        'keymap': 'combined_q3_q4_losses',
        'width': 12
    },
    'SOR': {
        'keymap': 'sor',
        'width': 5
    },
    'KPI': {
        'keymap': 'kpi',
        'width': 5
    },
    'WAB': {
        'keymap': 'wab',
        'width': 5
    },
    'BPI': {
        'keymap': 'bpi',
        'width': 5
    },
    'POM': {
        'keymap': 'pom',
        'width': 5
    },
    'T-Rank': {
        'keymap': 't_rank',
        'width': 5
    },
    'Conf': {
        'keymap': 'conf',
        'width': 20,
        'left_align': True
    },
    'NC Record': {
        'keymap': 'nc_record',
        'width': 9,
        'two_digit_text_year': True
    },
    'NC SOS': {
        'keymap': 'nc_sos',
        'width': 8
    },
    'Home Record': {
        'keymap': 'home_record',
        'width': 11,
        'two_digit_text_year': True
    },
    'Home Wins': {
        'keymap': 'home_wins',
        'width': 10
    },
    'Home Losses': {
        'keymap': 'home_losses',
        'width': 11
    },
    'Road Record': {
        'keymap': 'road_record',
        'width': 11,
        'two_digit_text_year': True
    },
    'Road Wins': {
        'keymap': 'road_wins',
        'width': 10
    },
    'Road Losses': {
        'keymap': 'road_losses',
        'width': 11
    },
    'Neutral Record': {
        'keymap': 'neutral_record',
        'width': 13,
        'two_digit_text_year': True
    },
    'Neutral Wins': {
        'keymap': 'neutral_wins',
        'width': 12
    },
    'Neutral Losses': {
        'keymap': 'neutral_losses',
        'width': 13
    },
    'Road/Neutral Wins': {
        'keymap': 'road_neutral_wins',
        'width': 16
    },
    'Road/Neutral Losses': {
        'keymap': 'road_neutral_losses',
        'width': 17
    },
    'Q1/Q2 Record': {
        'keymap': 'combined_q1_q2_record',
        'width': 13,
        'two_digit_text_year': True
    },
    'Q1/Q2 Wins': {
        'keymap': 'q1_q2_wins',
        'width': 11
    },
    'Q1/Q2 Losses': {
        'keymap': 'q1_q2_losses',
        'width': 12
    },
    'Q1 Record': {
        'keymap': 'q1_record',
        'width': 10,
        'two_digit_text_year': True
    },
    'Q1 Wins': {
        'keymap': 'q1_wins',
        'width': 8
    },
    'Q1 Losses': {
        'keymap': 'q1_losses',
        'width': 9
    },
    'Q2 Record': {
        'keymap': 'q2_record',
        'width': 9,
        'two_digit_text_year': True
    },
    'Q2 Wins': {
        'keymap': 'q2_wins',
        'width': 8
    },
    'Q2 Losses': {
        'keymap': 'q2_losses',
        'width': 9
    },
    'Q3 Record': {
        'keymap': 'q3_record',
        'width': 9,
        'two_digit_text_year': True
    },
    'Q3 Wins': {
        'keymap': 'q3_wins',
        'width': 8
    },
    'Q3 Losses': {
        'keymap': 'q3_losses',
        'width': 9
    },
    'Q4 Record': {
        'keymap': 'q4_record',
        'width': 9,
        'two_digit_text_year': True
    },
    'Q4 Wins': {
        'keymap': 'q4_wins',
        'width': 7
    },
    'Q4 Losses': {
        'keymap': 'q4_losses',
        'width': 9
    },
    'High Q1 Record': {
        'keymap': 'high_q1_record',
        'width': 14,
        'two_digit_text_year': True
    },
    'High Q1 Wins': {
        'keymap': 'high_q1_wins',
        'width': 12
    },
    'High Q1 Losses': {
        'keymap': 'high_q1_losses',
        'width': 13
    },
    'High Q1 R/N Record': {
        'keymap': 'high_q1_rn_record',
        'width': 18,
        'two_digit_text_year': True
    },
    'High Q1 R/N Wins': {
        'keymap': 'high_q1_rn_wins',
        'width': 14
    },
    'High Q1 R/N Losses': {
        'keymap': 'high_q1_rn_losses',
        'width': 18
    },
    'At Large Record': {
        'keymap': 'al_record',
        'width': 14,
        'two_digit_text_year': True
    },
    'At Large Wins': {
        'keymap': 'al_wins',
        'width': 13
    },
    'At Large Losses': {
        'keymap': 'al_losses',
        'width': 14
    },
    'Avg NET Wins': {
        'keymap': 'avg_net_wins',
        'width': 12
    },
    'Avg NET Losses': {
        'keymap': 'avg_net_losses',
        'width': 13
    },
}

X_WINS, Y_WINS, TIE = -1, 1, 0


def to_log(in_str):
    print(in_str)
    logging.info(in_str)


def record_to_wins_and_losses(in_record):
    in_split = in_record.split('-')
    return int(in_split[0].strip()), int(in_split[1].strip())


def compare_record(x_wins, x_losses, y_wins, y_losses, metric_pts, x_pts,
                   y_pts, new_record_comparison):
    if new_record_comparison:
        if x_wins > y_wins and x_wins > 0:
            x_pts += metric_pts
        elif y_wins > x_wins and y_wins > 0:
            y_pts += metric_pts
        elif x_wins == 0 and y_wins == 0:
            pass
        else:
            if x_losses < y_losses:
                x_pts += metric_pts
            elif y_losses < x_losses:
                y_pts += metric_pts
            else:
                to_log('      No points awarded due to W-L tie')
    else:
        if x_wins == 0 and y_wins > 0:
            y_pts += metric_pts
        elif y_wins == 0 and x_wins > 0:
            x_pts += metric_pts
        elif x_wins == 0 and y_wins == 0:
            pass
        else:
            r1_over_500 = x_wins - x_losses
            r2_over_500 = y_wins - y_losses

            if r1_over_500 > r2_over_500:
                x_pts += metric_pts
            elif r2_over_500 > r1_over_500:
                y_pts += metric_pts
            else:
                r1_winning_pct = 1.0 * x_wins / (x_wins + x_losses)
                r2_winning_pct = 1.0 * y_wins / (y_wins + y_losses)
                if r1_winning_pct > r2_winning_pct:
                    x_pts += metric_pts
                elif r2_winning_pct > r1_winning_pct:
                    y_pts += metric_pts
                elif x_wins > y_wins:
                    x_pts += metric_pts
                elif y_wins > x_wins:
                    y_pts += metric_pts

    return x_pts, y_pts


def compare_records(records_tup_list, x, y, x_pts, y_pts,
                    new_record_comparison):
    for metric_prefix, metric_pts in records_tup_list:
        x_pts, y_pts = compare_record(x[metric_prefix + '_wins'],
                                      x[metric_prefix + '_losses'],
                                      y[metric_prefix + '_wins'],
                                      y[metric_prefix + '_losses'], metric_pts,
                                      x_pts, y_pts, new_record_comparison)
        to_log(
            f'      {metric_prefix} record for {metric_pts} points ||| {x["team"]} {x_pts} - {y["team"]} {y_pts}'
        )

    return x_pts, y_pts


def compare_metric(x_metric, y_metric, metric_pts, x_pts, y_pts):
    if x_metric < y_metric:
        x_pts += metric_pts
    elif y_metric < x_metric:
        y_pts += metric_pts
    return x_pts, y_pts


def compare_metrics(metrics_tup_list, x, y, x_pts, y_pts):
    for metric_key, metric_pts in metrics_tup_list:
        x_pts, y_pts = compare_metric(x[metric_key], y[metric_key], metric_pts,
                                      x_pts, y_pts)
        to_log(
            f'      {metric_key} for {metric_pts} points ||| {x["team"]} {x_pts} - {y["team"]} {y_pts}'
        )

    return x_pts, y_pts


def compare_teams(x, y, formula):
    global SELECT_MODE

    x_pts, y_pts = 0.0, 0.0
    SELECT = 'SELECT_' if SELECT_MODE else ''

    METRICS_TUP_LIST = [
        ('sor', formula.get('SOR_PTS', 0)),
        ('combined_q3_q4_losses', formula.get('Q3_AND_Q4_PTS', 0)),
        ('q4_losses', formula.get('Q4_PTS', 0)),
        ('kpi', formula.get('KPI_PTS', 0)),
        ('wab', formula.get('WAB_PTS', 0)),
        ('nc_sos', formula.get('NC_SOS_PTS', 0)),
        ('bpi', formula.get(f'BPI_{SELECT}PTS', 0)),
        ('pom', formula.get(f'POM_{SELECT}PTS', 0)),
        ('t_rank', formula.get(f'T-RANK_{SELECT}PTS', 0)),
    ]


    RECORDS_TUP_LIST = [
        ('al', formula.get('WAALT_PTS', 0)),
        ('road_neutral', formula.get('ROAD_AND_NEUTRAL_PTS')),
        ('high_q1', formula.get('HIGH_Q1_PTS')),
        ('high_q1_rn', formula.get('HIGH_Q1_RN_PTS')),
        ('q1', formula.get('Q1_PTS')),
        ('q1_q2', formula.get('Q1_AND_Q2_PTS'))
    ]

    x_pts, y_pts = compare_metrics(METRICS_TUP_LIST, x, y, x_pts, y_pts)
    x_pts, y_pts = compare_records(RECORDS_TUP_LIST, x, y, x_pts, y_pts,
                                   formula.get('NEW_RECORD_COMPARISON', True))

    conf_leader_pts = formula.get('CONF_LEADER_PTS')
    if x['conf_leader']:
        x_pts += conf_leader_pts
    if y['conf_leader']:
        y_pts += conf_leader_pts

    bad_nc_sos_deduct_pts = formula.get('BAD_NC_SOS_DEDUCT_PTS')
    bad_nc_sos_deduct_thresold = formula.get('BAD_NC_SOS_DEDUCT_THRESHOLD')
    if x['nc_sos'] >= bad_nc_sos_deduct_thresold:
        x_pts -= bad_nc_sos_deduct_pts
    if y['nc_sos'] >= bad_nc_sos_deduct_thresold:
        y_pts -= bad_nc_sos_deduct_pts

    if x_pts > y_pts:
        point_diff = x_pts - y_pts
        point_suffix = 's' if point_diff > 1 else ''
        to_log(
            f'   {x["team"]} > {y["team"]} by {x_pts - y_pts} point{point_suffix} | ({x_pts} - {y_pts})'
        )
        return -1
    elif y_pts > x_pts:
        point_diff = y_pts - x_pts
        point_suffix = 's' if point_diff > 1 else ''
        to_log(
            f'   {y["team"]} > {x["team"]} by {y_pts - x_pts} point{point_suffix} | ({y_pts} - {x_pts})'
        )
        return 1
    else:
        if x['net'] < y['net']:
            to_log('   %s > %s due to NET ranking' % (x['team'], y['team']))
        else:
            to_log('   %s > %s due to NET ranking' % (y['team'], x['team']))
        return x['net'] - y['net']


def get_team_stats(in_team, at_large_teams):
    in_team = in_team.replace(' ', '-').replace("'",
                                                "").replace('&', '').replace(
                                                    '(', '').replace(')', '')
    team_url = TEAM_URL_TEMPLATE + in_team
    page = requests.get(team_url)
    team_hyperlink = f'=HYPERLINK("{team_url}", "{in_team}")'
    soup = BeautifulSoup(page.content, 'html.parser')
    tables = soup.find_all("table")

    al_wins, al_losses = 0, 0
    high_q1_wins, high_q1_losses = 0, 0
    high_q1_rn_wins, high_q1_rn_losses = 0, 0
    on_high_q1 = True
    idx_offset = {0: 63, 1: 64, 2: 68, 3: 69}
    ####### Need to find anchor for KPI on team page to get starting index
    ####### Then split on \n and parse
    kpi_idx = soup.text.find('KPI:\n')

    line_split = soup.text[kpi_idx:].split('\n')
    kpi = line_split[5].strip()
    sor = line_split[6].strip()
    wab = line_split[7].strip()
    ######################################
    bpi = line_split[19].strip()
    pom = line_split[20].strip()
    t_rank = line_split[21].strip()

    q1_idx = soup.text[kpi_idx:].find('H: 1-15 |')
    line_split = soup.text[kpi_idx + q1_idx:].split('\n')
    line_idx = 10
    while line_idx < len(line_split):
        line = line_split[line_idx]
        if line.isnumeric():
            location, opponent, team_score, opponent_score = line_split[
                line_idx + 1:line_idx + 5]
            if on_high_q1:
                if int(team_score) > int(opponent_score):
                    high_q1_wins += 1
                    if location in ('A', 'N'):
                        high_q1_rn_wins += 1
                else:
                    high_q1_losses += 1
                    if location in ('A', 'N'):
                        high_q1_rn_losses += 1

            if opponent in at_large_teams:
                if int(team_score) > int(opponent_score):
                    al_wins += 1
                else:
                    al_losses += 1
            line_idx += 8
        elif line.startswith('H: '):
            on_high_q1 = False
            line_idx += 10
        elif line == '':
            line_idx += 1
            continue
        elif line.startswith('Quadrant'):
            line_idx += 17
        elif line.startswith('Non-Division I Games'):
            break
        else:
            to_log(f'Unexpected line on {in_team} team sheet:')
            to_log(f'{line}')

    high_q1_record = '%s-%s' % (str(high_q1_wins), str(high_q1_losses))
    high_q1_rn_record = '%s-%s' % (str(high_q1_rn_wins),
                                   str(high_q1_rn_losses))
    al_record = '%s-%s' % (str(al_wins), str(al_losses))

    return team_hyperlink, kpi, sor, wab, bpi, pom, t_rank, high_q1_record, high_q1_wins, high_q1_losses, high_q1_rn_record, \
           high_q1_rn_wins, high_q1_rn_losses, al_record, al_wins, al_losses


def generate_output_file(sorted_input, jordan_formula, visible_columns):
    now_et = datetime.now(pytz.timezone('America/New_York'))
    today_str = now_et.strftime('%Y-%m-%d %H%M')
    eo_name = "selected" if SELECT_MODE else "sorted"
    fname = f"warrennolan_nitty_{'formula' if jordan_formula else 'net'}_{eo_name}_{today_str}.xlsx"
    to_log(f'Generating file at {os.getcwd()}\\{fname}')
    with xlsxwriter.Workbook(fname) as workbook:
        worksheet = workbook.add_worksheet()
        blue_cell_format = workbook.add_format({
            'bg_color': 'blue',
            'font_color': 'white',
            'align': 'center'
        })
        center_align_format = workbook.add_format({'align': 'center'})

        # write header row
        worksheet.write_row(0, 0, visible_columns)
        worksheet.set_row(0, None, center_align_format)

        for row_num, team_dict in enumerate(sorted_input):
            for col_num, col_name in enumerate(visible_columns):
                col_format = blue_cell_format if col_name == 'NET' and team_dict[
                    'conf_leader'] else {}
                col_key = COL_SETTINGS.get(col_name, {
                    'keymap': None
                }).get('keymap', None)
                if col_key:
                    worksheet.write(row_num + 1, col_num, team_dict[col_key],
                                    col_format)
                else:
                    to_log('!!! ERROR !!!')
                    to_log(f'No valid key mapping exists for {col_name}')

        col_prefix, col_suffix = '', 'A'
        cols_to_ignore_two_digit_text_year = []
        for col_name in visible_columns:
            col_letter = col_prefix + col_suffix
            left_align = COL_SETTINGS[col_name].get('left_align', False)
            worksheet.set_column(
                f'{col_letter}:{col_letter}', COL_SETTINGS[col_name]['width'],
                center_align_format if not left_align else None)
            if COL_SETTINGS[col_name].get('two_digit_text_year', False):
                cols_to_ignore_two_digit_text_year.append(col_letter)
            if col_suffix == 'Z':
                col_prefix, col_suffix = 'A', 'A'
            else:
                col_suffix = chr(ord(col_suffix) + 1)

        worksheet.freeze_panes(1, 2)
        two_digit_str_list = [
            f'{col_name}2:{col_name}1000'
            for col_name in cols_to_ignore_two_digit_text_year
        ]
        two_digit_str = ' '.join(two_digit_str_list)
        worksheet.ignore_errors({'two_digit_text_year': two_digit_str})

    return fname


def get_net_nitty_raw_data():
    page = requests.get(MEN_URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    tables = soup.find_all("table")
    table = tables[0]
    return [[(cell.text, cell.attrs.get('style', ''))
             for cell in row.find_all(["th", "td"])]
            for row in table.find_all("tr")]


def cleanse_team_data(row):
    cleansed_row, conf_leader, ineligible = [], False, False

    for idx, cell_tup in enumerate(row):
        cell, cell_style = cell_tup
        if idx == 0:
            if 'background-color:Blue' in cell_style:
                conf_leader = True
            if 'background-color:Black' in cell_style:
                ineligible = True
        if cell in ['\n', '\n\n']:
            continue
        while cell[0] == '\n':
            cell = cell[1:]
        if idx == 1:
            cell_split = cell.split('\n')
            open_parenthesis_idx = cell_split[1].find('(')
            team, conf, conf_record = cell_split[0], cell_split[
                1][:open_parenthesis_idx -
                   1], cell_split[1][open_parenthesis_idx + 1:].replace(
                       ')', '')
            cleansed_row.extend([team, conf, conf_record])
        elif idx == 2:
            continue
        else:
            cleansed_row.append(cell.strip())

    return cleansed_row, conf_leader, ineligible


def create_team_data_obj(cleansed_team_data, conf_leader, at_large_teams,
                         ineligible_teams, ineligible):
    global SELECT_TEAMS
    global SELECT_MODE

    team_data_obj = None
    net, team, conf, conf_record, overall_record, sos, nc_record, nc_sos, home_record, road_record, neutral_record, q1_record, q2_record, q3_record, q4_record, avg_net_wins, avg_net_losses = cleansed_team_data

    if not ineligible and team not in ineligible_teams and (not SELECT_MODE or team in SELECT_TEAMS):
        to_log('   Getting {team} Stats'.format(team=team))
        team_url, kpi, sor, wab, bpi, pom, t_rank, high_q1_record, high_q1_wins, high_q1_losses, high_q1_rn_record, high_q1_rn_wins, high_q1_rn_losses, al_record, al_wins, al_losses = get_team_stats(
            team, at_large_teams)
        home_wins, home_losses = record_to_wins_and_losses(home_record)
        road_wins, road_losses = record_to_wins_and_losses(road_record)
        neutral_wins, neutral_losses = record_to_wins_and_losses(
            neutral_record)
        q1_wins, q1_losses = record_to_wins_and_losses(q1_record)
        q2_wins, q2_losses = record_to_wins_and_losses(q2_record)
        q3_wins, q3_losses = record_to_wins_and_losses(q3_record)
        q4_wins, q4_losses = record_to_wins_and_losses(q4_record)
        road_neutral_wins = road_wins + neutral_wins
        road_neutral_losses = road_losses + neutral_losses
        combined_road_neutral_record = '%i-%i' % (road_neutral_wins,
                                                  road_neutral_losses)
        q1_q2_wins = q1_wins + q2_wins
        q1_q2_losses = q1_losses + q2_losses
        combined_q1_q2_record = '%i-%i' % (q1_wins + q2_wins,
                                           q1_losses + q2_losses)
        combined_q3_q4_losses = q3_losses + q4_losses
        team_data_obj = {
            'team': team,
            'team_url': team_url,
            'net': int(net.split(' ')[0]),
            'conf': conf,
            'conf_record': conf_record,
            'overall_record': overall_record,
            'kpi': int(kpi) if kpi else 1000,
            'sor': int(sor) if sor else 1000,
            'wab': int(wab) if wab else 1000,
            'bpi': int(bpi) if bpi else 1000,
            'pom': int(pom) if pom else 1000,
            't_rank': int(t_rank) if t_rank else 1000,
            'nc_record': nc_record,
            'nc_sos': int(nc_sos) if nc_sos else 1000,
            'home_record': home_record,
            'home_wins': home_wins,
            'home_losses': home_losses,
            'road_record': road_record,
            'road_wins': road_wins,
            'road_losses': road_losses,
            'neutral_record': neutral_record,
            'neutral_wins': neutral_wins,
            'neutral_losses': neutral_losses,
            'road_neutral_wins': road_neutral_wins,
            'road_neutral_losses': road_neutral_losses,
            'combined_road_neutral_record': combined_road_neutral_record,
            'q1_q2_wins': q1_q2_wins,
            'q1_q2_losses': q1_q2_losses,
            'combined_q1_q2_record': combined_q1_q2_record,
            'combined_q3_q4_losses': combined_q3_q4_losses,
            'q1_record': q1_record,
            'q1_wins': q1_wins,
            'q1_losses': q1_losses,
            'q2_record': q2_record,
            'q2_wins': q2_wins,
            'q2_losses': q2_losses,
            'q3_record': q3_record,
            'q3_wins': q3_wins,
            'q3_losses': q3_losses,
            'q4_record': q4_record,
            'q4_wins': q4_wins,
            'q4_losses': q4_losses,
            'high_q1_record': high_q1_record,
            'high_q1_wins': high_q1_wins,
            'high_q1_losses': high_q1_losses,
            'high_q1_rn_record': high_q1_rn_record,
            'high_q1_rn_wins': high_q1_rn_wins,
            'high_q1_rn_losses': high_q1_rn_losses,
            'al_record': al_record,
            'al_wins': al_wins,
            'al_losses': al_losses,
            'avg_net_wins': avg_net_wins,
            'avg_net_losses': avg_net_losses,
            'conf_leader': conf_leader
        }
    else:
        to_log(f'   Skipping {team} due to ineligibility and/or not being SELECTED')

    return team_data_obj


def extract_team_data(row, at_large_teams, ineligible_teams):
    team_data_obj = None
    if not row[0][0].startswith('NET\n'):
        cleansed_team_data, conf_leader, ineligible = cleanse_team_data(row)
        team_data_obj = create_team_data_obj(cleansed_team_data, conf_leader,
                                             at_large_teams, ineligible_teams,
                                             ineligible)

    return team_data_obj


def splice_in_team_dict(team_dict, out_list, team_dict_idx):
    if team_dict_idx == 0:
        out_list = [team_dict] + out_list
    elif team_dict_idx == len(out_list):
        out_list.append(team_dict)
    else:
        out_list = out_list[:team_dict_idx] + [team_dict
                                               ] + out_list[team_dict_idx:]

    return out_list


def get_team_set_from_file(filename):
    team_set = set()

    if os.path.exists(filename):
        with open(filename) as team_file:
            for team_name in team_file.readlines():
                team_set.add(team_name.replace('\n', ''))
    else:
        to_log(
            '*******************************************************************'
        )
        to_log(
            '   %s FILE NOT FOUND. I will behave as if the file exists but is empty.'
            % filename)
        to_log(
            '*******************************************************************'
        )

    return team_set


def sort_teams(in_list, formula):
    out_list = []
    log_bottom_list = []
    for idx, team_dict in enumerate(in_list):
        team_name = team_dict['team']
        to_log(' Placing %s' % team_name)
        overall_wins, overall_losses = record_to_wins_and_losses(
            team_dict['overall_record'])
        if overall_wins - overall_losses < 2 and not team_dict['conf_leader']:
            # only consider teams at least 2 games over .500, or conference leaders
            to_log('%s filtered out due to %s overall record' %
                   (team_name, team_dict['overall_record']))
        else:
            net_rank = idx + 1
            if net_rank == 1:
                out_list.append(team_dict)
            else:
                team_dict_idx = 0
                for out_list_idx, team_to_cmp in enumerate(out_list[::-1]):
                    out_list_idx = len(out_list) - 1 - out_list_idx
                    if compare_teams(team_dict, team_to_cmp, formula) > 0:
                        # team_to_cmp is better. team_dict should go just below them
                        team_dict_idx = out_list_idx + 1
                        break

                out_list = splice_in_team_dict(team_dict, out_list,
                                               team_dict_idx)

    for log_bottom_msg in log_bottom_list:
        to_log(log_bottom_msg)

    return out_list


def do_the_work():
    global SELECT_MODE
    global SELECT_TEAMS

    config_file = 'config.txt'
    fname = None
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            logging.basicConfig(level=logging.INFO,
                                filename=LOG_FNAME,
                                filemode='w',
                                format='%(message)s')
            team_dict_list = []
            ineligible_teams = set(config.get('INELIGIBLE', []) or [])
            at_large_teams = set(config.get('AT_LARGE', []) or [])
            raw_table_data = get_net_nitty_raw_data()

            use_jordan_formula = 'JORDAN_FORMULA' in config and config['JORDAN_FORMULA'].get('ENABLED', False)
            visible_columns = config.get('VISIBLE_COLUMNS', [])

            if use_jordan_formula:
                SELECT_MODE = config['JORDAN_FORMULA'].get('SELECT_MODE', False)
                SELECT_TEAMS = set(config.get('SELECTED', []) or [])

            to_log('Getting all team stats')
            for row in raw_table_data[1:]:
                team_data = extract_team_data(row, at_large_teams, ineligible_teams)
                if team_data:
                    team_dict_list.append(team_data)

            if not visible_columns:
                to_log('No VISIBLE_COLUMNS specified. Doing nothing, buh bye.')
            elif use_jordan_formula:
                to_log('\n\nSorting results and writing to file\n')
                sorted_team_list = sort_teams(team_dict_list, config['JORDAN_FORMULA'])
                fname = generate_output_file(sorted_team_list, use_jordan_formula,
                                     visible_columns)
            else:
                to_log('\n\nWriting results to file\n')
                fname = generate_output_file(team_dict_list, use_jordan_formula,
                                     visible_columns)

            to_log('All done. Go back to /status page to get results.')
    else:
        to_log('The config.yaml file is missing. Doing nothing, buh bye.')

    return fname, LOG_FNAME


app = Flask(__name__)

OUTPUT_FILENAME = None
LOG_FILENAME = None
processing_status = {"done": False, "file_ready": False}

def create_excel_file():
    global processing_status
    global OUTPUT_FILENAME
    global LOG_FILENAME

    processing_status["done"] = False

    directory = Path(".")
    for file in directory.glob("warren*xlsx"):
        if file.is_file():
            file.unlink()

    OUTPUT_FILENAME, LOG_FILENAME = do_the_work()

    # Mark as done
    processing_status["done"] = True
    processing_status["file_ready"] = True


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded", 400
        file = request.files["file"]
        if file.filename == "":
            return "No selected file", 400
        elif file.filename != "config.txt":
            return "File must be named config.txt", 400

        input_filepath = os.path.join(os.getcwd(), file.filename)
        file.save(input_filepath)

        # Start processing in a separate thread
        thread = threading.Thread(target=create_excel_file)
        thread.start()

        return '''
        <h1>File is being processed...</h1>
        <p>Check status: <a href="/status">Click here</a></p>
        '''

    return '''
    <!doctype html>
    <html>
        <body>
            <h1>Upload Input File</h1>
            <form action="/" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <input type="submit" value="Upload and Process">
            </form>
        </body>
    </html>
    '''


@app.route("/status")
def check_status():
    """Endpoint to check if the file is ready for download."""
    if processing_status["file_ready"]:
        return '''
        <h1>Processing complete!</h1>
        <p><a href="/download_excel">Download Excel</a></p>
        <p><a href="/download_log">Download Log</a></p>
        '''
    return '''
        <h1>Processing...</h1><p>Please wait and refresh this page.</p>
    '''


@app.route("/download_excel")
def download_excel_file():
    """Download the processed Excel file."""
    global OUTPUT_FILENAME

    if not processing_status["file_ready"]:
        return "File is not ready yet. Check status at /status", 400
    return send_file(OUTPUT_FILENAME, as_attachment=True)

@app.route("/download_log")
def download_log_file():
    global LOG_FILENAME

    if not processing_status["file_ready"]:
        return "File is not ready yet. Check status at /status", 400
    return send_file(LOG_FILENAME, as_attachment=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
