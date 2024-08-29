import pandas as pd
import time
import logging
import configparser
import os

# Setup logging
logging.basicConfig(
    filename='recommendation_engine.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration from a file
config = configparser.ConfigParser()
config.read('config.ini')

# Configuration parameters
INPUT_FILE = config['FILES']['InputFile']
USERNAMES_FILE = config['FILES']['UsernamesFile']
OUTPUT_FILE = config['FILES']['OutputFile']
RECOMMENDATIONS_OUTPUT_FILE = config['FILES']['RecommendationsOutputFile']
TOP_N = int(config['RECOMMENDATIONS']['TopN'])
SLEEP_TIME = int(config['SETTINGS']['SleepTime'])

# Weights for each field (can be configured in config.ini)
weights = {
    'view_count': float(config['WEIGHTS']['ViewCount']),
    'rating_count': float(config['WEIGHTS']['RatingCount']),
    'upvote_count': float(config['WEIGHTS']['UpvoteCount']),
    'share_count': float(config['WEIGHTS']['ShareCount']),
    'comment_count': float(config['WEIGHTS']['CommentCount'])
}

def load_data():
    try:
        data = pd.read_csv(INPUT_FILE, index_col='id')
        return data
    except Exception as e:
        logging.error(f"Error loading data from {INPUT_FILE}: {e}")
        raise

def load_usernames():
    try:
        usernames_data = pd.read_csv(USERNAMES_FILE)
        return usernames_data
    except Exception as e:
        logging.error(f"Error loading usernames from {USERNAMES_FILE}: {e}")
        raise

def generate_recommendations():
    try:
        data = load_data()
        usernames_data = load_usernames()

        # Normalize weights if they don't sum to 1.0
        total_weight = sum(weights.values())
        if total_weight != 1.0:
            normalized_weights = {k: v / total_weight for k, v in weights.items()}
            logging.info(f"Normalized weights to sum up to 1.0: {normalized_weights}")
        else:
            normalized_weights = weights

        # Calculate the popularity score
        data['popularity_score'] = (
            normalized_weights['view_count'] * data['view_count'] +
            normalized_weights['rating_count'] * data['rating_count'] +
            normalized_weights['upvote_count'] * data['upvote_count'] +
            normalized_weights['share_count'] * data['share_count'] +
            normalized_weights['comment_count'] * data['comment_count']
        )

        # Sort IDs based on popularity score
        recommended_ids = data[['popularity_score']].sort_values(by='popularity_score', ascending=False).reset_index()

        # Save the recommendations
        recommended_ids.to_csv(OUTPUT_FILE, index=False)
        logging.info(f"Recommendations complete. Sorted IDs saved to {OUTPUT_FILE}")

        # Identify users with no ID history and generate recommendations
        users_with_no_history = usernames_data[~usernames_data['id'].isin(data.index)]
        recommendations = []
        for _, user_row in users_with_no_history.iterrows():
            user_id = user_row['username']
            top_recommendations = recommended_ids.head(TOP_N)
            for _, video_row in top_recommendations.iterrows():
                video_id = video_row['id']
                recommendations.append({'username': user_id, 'recommended_id': video_id})
                # Print the username and recommended ID to the output screen
                print(f"Username: {user_id}, Recommended ID: {video_id}")

        # Save the user recommendations
        recommendations_df = pd.DataFrame(recommendations)
        recommendations_df.to_csv(RECOMMENDATIONS_OUTPUT_FILE, index=False)
        logging.info(f"User recommendations complete. Recommendations saved to {RECOMMENDATIONS_OUTPUT_FILE}")

    except Exception as e:
        logging.error(f"Error generating recommendations: {e}")
        raise

def run_recommendation_engine():
    print("Starting the recommendation engine...")  # Indicate that the engine has started
    processed_users = set()  # Set to keep track of processed usernames

    while True:
        try:
            print("Loading usernames data...")
            usernames_data = load_usernames()
            current_users = set(usernames_data['username'])

            # Check for new users
            new_users = current_users - processed_users

            if new_users:
                print(f"New users detected: {new_users}. Restarting the recommendation engine.")
                logging.info(f"New users detected: {new_users}. Restarting the recommendation engine.")
                generate_recommendations()
                processed_users = current_users  # Update processed users after generating recommendations
                print("Recommendation engine completed processing new users.")
            else:
                print("No new users detected. No need to restart the engine.")
                logging.info("No new users detected. No need to restart the engine.")

        except Exception as e:
            print(f"Error in recommendation engine loop: {e}")
            logging.error(f"Error in recommendation engine loop: {e}")
        finally:
            print(f"Sleeping for {SLEEP_TIME} seconds before next check...")
            time.sleep(SLEEP_TIME)  # Wait before checking again

# Start the scheduler
run_recommendation_engine()
