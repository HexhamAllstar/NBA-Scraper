import pandas as pd
import numpy as np
import matplotlib.patches as patches # import patches so we can create a rectangle of greycolor
from math import gcd
import matplotlib.lines
import seaborn as sns
import matplotlib.pyplot as plt
import backend
from matplotlib.colors import ListedColormap

# grab results & boxscore data from SQL tables using backend function
results_data = backend.retrieve_all_results() # SQL statement 'SELECT * from results'
boxscore_data = backend.retrieve_all_boxscores() # SQL statement 'SELECT * from boxscores'

# get a list of unique team names
team_names = list(results_data['HomeTeam'].unique())
team_names.remove('Team LeBron') # remove Lebron's all-star team
team_names.remove(' ') # blank team due to USA vs world game on all-star weekend

# Define functions to process results data
def get_team_games(team_name):
    """Takes in a string of a team name and returns a dataframe of all games this team played in."""
    if team_name in team_names: #if the entered team name is valid
        df = results_data[(results_data['HomeTeam'] == team_name) | (results_data['AwayTeam'] == team_name)].copy()
        df.sort_values(by='GameDate', ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    else:
        print('That name is not valid, please enter a valid team name (case sensitive)')

def calc_wins(row, team_name):
    """This function takes in a row of a dataframe and a team name and returns a column called 'Win' that is
    equal to 1 if the specified team won and -1 if the specified team lost."""
    # first check to see if the team name is valid and in this dataframe
    if (team_name in team_names) & (team_name in [row['HomeTeam'],row['AwayTeam']]):
        # then calculate whether the team of interest won or not
        if (row['HomeTeam'] == team_name) & (int(row['HomeScore']) > int(row['AwayScore'])) :
            row['Win'] = 1
        elif (row['AwayTeam'] == team_name) & (int(row['AwayScore']) > int(row['HomeScore'])) :
            row['Win'] = 1
        else:
            row['Win'] = -1
        return row
    else:
        print('Invalid team name')

def add_win_col(df, team_name):
    df = df.apply(calc_wins, args=(team_name,), axis=1)
    return df

def add_plus_minus(df):
    """Takes in a df with 'Win' column (+1 for win, -1 for loss) and adds a
    '+/-' column showing the cumulative sum of the wins column"""
    df['+/-'] = df['Win'].cumsum()
    return df

def add_game_number(df):
    """Adds a column 'GameNumber' to a df with games sorted by date (oldest game first)."""
    df['GameNumber'] = df.index + 1
    return df

# create pipeline for results data
def results_pipeline(team_name):
    """Takes in a string of the team name (case sensitive) and plots the +/- of the team for every game in the database.
    """
    # First check if the team name is valid
    if team_name in team_names:
        # then call the sequence of functions defined above
        df = get_team_games(team_name)
        df = df.apply(calc_wins, args=(team_name,), axis=1)
        df = add_plus_minus(df)
        df = add_game_number(df)
    return df

# define functions to process boxscore data
def get_team_boxscores(team_name):
    """For a given team name string, returns a dataframe containing all boxscores relating to players
    from the team."""
    # check validity of team name
    if team_name in team_names:
        df = boxscore_data[boxscore_data['Team'] == team_name]
        return df
    else:
        print('Invalid team name')

def get_minutes_stats(df):
    """For a given dataframe, retains the Player Name, FGM, Min, Starter and GameID columns."""
    df = df[['Player Name','FGM','Min','Starter','GameID']]
    return df

def get_boxscore_dates(df):
    """Takes in a dataframe with a GameID column and uses a left inner join with the results dataframe to add the
    corresponding GameDate"""
    df = pd.merge(df, results_data[['GameID','GameDate']], on = 'GameID')
    # join on GameID as that's the common column between the 2 dataframes
    df.sort_values(by='GameDate', inplace=True)
    # sort by date and return
    return df

def dnp_reason(row):
    """Takes in a row of a dataframe, creating a new column called 'DNP Reason' which is zero
    if the player played and otherwise contains a reason for the player not playing. If the player didn't
    play then their minutes and FGM columns are set to zero"""
    reason = row['FGM']
    try :
        # if the reason column casts as an int, then the player must have played
        reason = int(reason)
        # players that played don't have a DNP reason
        row['DNP Reason'] = 0
    except ValueError:
        # if it can't be cast as an int then it must be a string
        row['FGM'] = 0 # put a zero in the FGM column
        row['Min'] = '0:0' # keep minutes format same as other rows for now
        # splitting the string by spaces returns the reason in index 2
        if reason == '':
            row['DNP Reason'] = 0
        elif reason.split(' ')[2] == 'Injury/Illness':
            row['DNP Reason'] = 'Injury/Illness'
        elif reason.split(' ')[2] == "Coach's":
            row['DNP Reason'] = 0
        else:
            row['DNP Reason'] = 'Other'
    return row

def convert_mins_decimal(row):
    """Takes in a dataframe row with a 'Min' column of format 'mm:ss' and converts it to decimal minutes."""
    min_string = row['Min']
    minutes = float(min_string.split(':')[0]) # minutes contained in string before the ':'
    seconds = float(min_string.split(':')[1])/60 # seconds contained after the ':', divide by 60 for decimal seconds
    row['Min'] = round(minutes+seconds, 2) # add together and round to 2 dp
    return row

def  create_plotting_df(df):
    """Takes a teams boxscore dataframe and groups by player name, summing the minutes column and sorting
    players by total minutes played in the season."""
    plotting_df = df.groupby(by='Player Name').sum()[['Min']].sort_values(by='Min', ascending=False)
    plotting_df.reset_index(inplace=True) # reset index so we get integer indexes

    return plotting_df

def get_boxscore_gamenum(df):
    """Takes in a dataframe with a date column and assigns an integer game number based on the chronological order."""
    game_dates = df['GameDate'].unique()
    date_dict = {}
    count=1 # count begins at 1 because the first date is the date of the first game
    for date in game_dates:
        date_dict[date] = count # create a mapping 'date':GameNumber
        count +=1 # increment count and move to next date

    df['GameNumber'] = df['GameDate'].map(date_dict)
    # create a new column which is the GameDate column mapped using the dictionary created

    return df

def create_blanks_plotting(plotting_df, boxscores_df):
    """Takes in a plotting df which consists of a teams player name and total minutes played in the season,
    then adds a column of zeros per game"""
    for num in boxscores_df['GameNumber'].unique():
        plotting_df[num] = 0

    return plotting_df

def get_minutes_dates(row, boxscores_df):
    """Takes in a row containing a player name for a team and returns columns containing the players
    minutes played for each game the team has played. If the player doesn't appear in the boxscore for a game,
    their minutes are set to zero"""

    player = row['Player Name']
    for num in boxscores_df['GameNumber'].unique():
        mins = boxscores_df[(boxscores_df['Player Name'] == player) & (boxscores_df['GameNumber'] == num)]['Min']
        # mins contains an empty list if the player doesn't appear in the boxscore for that game
        if len(mins.values) == 0 :
            row[num] = 0
        else:
            # if the player does appear then take the minutes value
            row[num] = mins.values[0]
    return row

def get_annots(row, boxscores_df):
    """Takes in a row with a player name and for each game, checks if the player was a starter or had a DNP reason in the boxscore dataframe.
    A DNP reason of Injury/Illness will be represented with a '/', and a starter will be represented by '-'."""
    player = row['Player Name']
    for num in boxscores_df['GameNumber'].unique():
        starter = boxscores_df[(boxscores_df['Player Name'] == player) & (boxscores_df['GameNumber'] == num)]['Starter']
        dnp = boxscores_df[(boxscores_df['Player Name'] == player) & (boxscores_df['GameNumber'] == num)]['DNP Reason']
        if len(dnp) == 0: # this player wasn't in the boxscore
            row[num] = '' # no annotation
        elif starter.values[0] == 1: # this player was a starter
            row[num] = '=' # insert annotation
        elif dnp.values[0] == 'Injury/Illness': # this player was injured
            row[num] = '/' # insert annotation
        else:
            row[num] = '' # this player did not start and was not injured
            pass

    return row

def get_nwt(row, boxscores_df):
    """Given a row with a player name in, returns a 1 in games where the player was not in the boxscore and a zero
    if they were in the box score"""
    player = row['Player Name']
    for num in boxscores_df['GameNumber'].unique():
        boxscore_row = boxscores_df[(boxscores_df['Player Name'] == player) & (boxscores_df['GameNumber'] == num)]
        if len(boxscore_row) == 0:
            row[num] = 1
        else:
            row[num] = 0
    return row

def create_proxy(label):
    line = matplotlib.lines.Line2D([0], [0], linestyle='none', mfc='black',
                mec='none', marker=r'$\mathregular{{{}}}$'.format(label))
    return line

def plot_heatmap(games_df, boxscores_df, plotting_df, annot_df, mask_df, team_name):
    """Takes in the results dataframe for a particular team, the boxscores df for that team,
    the annotation dataframe, plotting dataframe and the mask dataframe,
    along with  the string of the team name, and plots the complete heatmap"""

    fig = plt.figure(figsize=(10,8)) # define the size of the canvas to plot on
    ax=fig.add_subplot(111, label="1") # define an axis object so we can copy it

    annot_kws = {"size":12, "color":"grey", "weight":"bold"} # formatting choices for the annotations

    # first plot our actual heatmap
    sns.heatmap(plotting_df.drop(['Player Name','Min'], axis=1),xticklabels=2, ax=ax,
                yticklabels=plotting_df['Player Name'], linewidths=1, linecolor='black',
                cbar_kws={'label':'Minutes played', 'orientation':'horizontal'}, cmap='YlOrRd',
               annot=annot_df.drop(['Player Name','Min'], axis=1),fmt='', annot_kws=annot_kws)

    # now plot the masked dataframe, specifying the colors for value 0 and 1, and specifying mask when the value is less than 1
    sns.heatmap(mask_df.drop(['Player Name','Min'], axis=1), ax=ax,
                mask=mask_df.drop(['Player Name','Min'], axis=1)<1,
                cmap=ListedColormap(['grey', 'grey']), linewidths=1,
                linecolor='black', cbar=False ,yticklabels=plotting_df['Player Name'])

    # now copy the axis and plot the line plot
    ax2=ax.twinx() # copy axis
    ax2.axhline(y=0, color='black', linewidth=10, zorder=-1) # create a horizontal line at y=0 for reference
    ax2.plot([0] + list(games_df['GameNumber']), [0] + list(games_df['+/-']),
             drawstyle='steps-post', linewidth=6, zorder=1) # plot the line
    ax2.set_ylabel('Wins minus Losses') # define the y label
    ax2.yaxis.tick_right() # set the ticks to appear on the RHS
    ax2.yaxis.set_label_position('right') # set the label to appear on the right

    # code to set the yticks for the line plot
    # find the maximum value so we can set the yrange relative to that
    absmaxval = games_df['+/-'].abs().max()
    # if the value is even, add 2 to it so we have an even range above and below zero
    if absmaxval % 2 == 0:
        hcf = gcd(2*(absmaxval + 2), len(list(plotting_df['Player Name'].unique())))
        # use the highest common factor plus one to make sure we are plotting integers
        # this only works if there are an even number of players
        # need to pad for teams that have an odd number of players
        ax2.yaxis.set_ticks(np.linspace(-1*(absmaxval + 2), (absmaxval + 2), num=hcf+1))

    else:
        # if the value is odd, add 3 to make it even
        hcf = gcd(2*(absmaxval + 3), len(list(plotting_df['Player Name'].unique())))
        # use the highest common factor plus one to make sure we are plotting integers
        # this only works if there are an even number of players
        # need to pad for teams that have an odd number of players
        ax2.yaxis.set_ticks(np.linspace(-1*(absmaxval + 3), (absmaxval + 3), num=hcf+1))
    ax2.grid(False) # don't display the grid for the lineplot

    # code for the custom legend
    labels = ['=','/'] # the markers used for the 2 annotations
    descriptions = ['Starter','Injured/Ill', 'Not in boxscore', 'Win/Loss']

    proxies = [create_proxy(item) for item in labels]

    line = matplotlib.lines.Line2D([0], [0], mfc='blue', linewidth=6)
    ax2.legend(proxies + [patches.Rectangle((0,0),1,1,facecolor='grey')] + [line], descriptions, numpoints=1,
               markerscale=2, loc='center left', bbox_to_anchor=(1.05, 1))

    # custom title that includes wins and losses
    losses = (len(list(games_df['GameNumber'])) - list(games_df['+/-'])[-1])/2
    wins = losses + list(games_df['+/-'])[-1]
    fig.suptitle('Minutes for ' + team_name + ' rotation, current record: ' + str(int(wins)) + '-' + str(int(losses)) , y=1.0)

    plt.xlabel('Game Number')
    plt.savefig('images/' + team_name + '.png', bbox_inches='tight')
    plt.close

# create pipeline for processing and plotting
def heatmap_pipeline(team_name):
    """This function takes in a string of a team name and plots the complete heatmap
    for that team."""
    if team_name not in team_names:
        print('Invalid team name')
    else:
        print('Generating plot for ' + team_name)
        games_df = results_pipeline(team_name)
        boxscores_df = get_team_boxscores(team_name)
        boxscores_df = get_minutes_stats(boxscores_df)
        boxscores_df = get_boxscore_dates(boxscores_df)
        boxscores_df = boxscores_df.apply(dnp_reason, axis=1)
        boxscores_df = boxscores_df.apply(convert_mins_decimal, axis=1)
        plotting_df = create_plotting_df(boxscores_df)

        # if there's an odd number of players then add a blank row so that our plot works
        if len(plotting_df['Player Name'].unique()) % 2 != 0:
            plotting_df = plotting_df.append({'Player Name':' ', 'Min':0}, ignore_index=True)
        else:
            pass

        boxscores_df = get_boxscore_gamenum(boxscores_df)
        plotting_df = create_blanks_plotting(plotting_df, boxscores_df)
        plotting_df = plotting_df.apply(get_minutes_dates,args=(boxscores_df,), axis=1)
        annot_df = plotting_df.apply(get_annots, args=(boxscores_df,), axis=1)
        mask_df = annot_df.apply(get_nwt, args=(boxscores_df,), axis=1)

        plot_heatmap(games_df, boxscores_df, plotting_df, annot_df, mask_df, team_name)
