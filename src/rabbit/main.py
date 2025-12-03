import pandas as pd

from .sources import GitHubAPIExtractor
from .predictor import predict_user_type
from .sources.errors import GitHubAPIError

from rich.progress import track

def _save_results(all_results, output_type, save_path):
    """
    args: all_results (DataFrame)- all the results (contributor name, type, confidence and so on) and additional information (features used to determine the type)
          save_path (str) - the path along with file name and extension to save the results
          output_type (str) - to convert the results to csv or json

    returns: None

    description: Save the results in the given path
    """

    if output_type == 'text':
        print(all_results.to_string(index=False))

    elif output_type == 'csv':
        all_results.to_csv(save_path, index=False)
    elif output_type == 'json':
        all_results.to_json(save_path, orient='records', indent=4)


def run_rabbit(
        contributors: list[str],
        api_key: str = None,
        min_events: int = 5,
        min_confidence: float = 1.0,
        max_queries: int = 3,
        output_type: str = 'text',
        output_path: str = '',
        _verbose: bool = False,
        incremental: bool = False,
):
    """
    Orchestrates the RABBIT bot identification process for GitHub contributors.

    Args:
        contributors (list[str]): A list of GitHub contributor login names to analyze.
        api_key (str, optional): GitHub API key for authentication. Defaults to None.
        min_events (int, optional): Minimum number of events required to analyze a contributor. Defaults to 5.
        min_confidence (float, optional): minimum confidence on type of contributor to stop further querying. Defaults to 1.0.
        max_queries (int, optional): Maximum number of API queries allowed per contributor. Defaults to 3.
        output_type (str, optional): Format for saving results ('text', 'csv', or 'json'). Defaults to 'text'.
        output_path (str, optional): Path to save the output file. Defaults to an empty string.
        _verbose (bool, optional): If True, displays the features that were used to determine the type of contributor. Defaults to False.
        incremental (bool, optional): Update the output file/print on terminal once the type is determined for new contributors. If False, results will be accessible only after the type is determined for all the contributors Defaults to False.

    Returns:
        None

    Description:
        Processes each contributor by:
        1. Querying GitHub Events API to fetch events.
        2. Computing activity sequences from the events. (using ghmap)
        3. Extracting features from the activity sequences.
        4. Predicting whether the contributor is a bot or human based on the features.
        5. Saving the results in the specified format and location.
    """

    gh_api_client = GitHubAPIExtractor(api_key=api_key, max_queries=max_queries)

    all_results = pd.DataFrame()
    for contributor in track(contributors, description="Processing contributors..."):
        result = None
        try:
            events = gh_api_client.query_events(contributor)
            if len(events) < min_events:
                result = {"contributor": contributor, "type": "Unknown", "confidence": "-"}
            else:
                user_type, confidence = predict_user_type(contributor, events)
                result = { "contributor": contributor, "type": user_type, "confidence": confidence }

        except GitHubAPIError as github_err:
            print(github_err)
        except Exception as e:
            print(f"An unexpected error occurred for contributor {contributor}: {e}")
        finally:
            if result is None:
                result = {"contributor": contributor, "type": "Invalid", "confidence": "-"}
            all_results = pd.concat([all_results, pd.DataFrame([result])], ignore_index=True)

            if incremental:
                _save_results(all_results, output_type, output_path)

    if not incremental:
        _save_results(all_results, output_type, output_path)

