import requests
import json
import urllib.parse
import time
from typing import Optional, Dict
import logging
import os

logger = logging.getLogger(__name__)

class Agent_Bridge:
    """Class to handle communicating with the MoDSAgent servlet via a
    series of HTTP requests.
    """

    # Polling interval when waiting or jobs to finish (seconds)
    POLL_INTERVAL: int = 10

    # Maximum number of requests when waiting for jobs to finish
    MAX_ATTEMPTS: int = 60

    # Base URL for HTTP requests
    BASE_URL: str = f"{os.environ['MODS_AGENT_BASE_URL']}/"

    # Additional URL part for job submission
    SUBMISSION_URL_PART: str = "request?query="

    # Additional URL part for requesting job outputs
    OUTPUT_URL_PART: str = "output/request?query="

    # ID of generated job
    jobID: Optional[str] = None

    def runJob(self, jsonString: str)->Optional[Dict]:
        """Runs a complete MoDS simulation on a remote machine via use of HTTP requests.
        Note that this method will block until the remote job is completed and has returned
        a result or error message.

        Arguments:
            jsonString -- JSON input data string

        Returns:
            Resulting JSON data objects (or None if error occurs)
        """
        logger.info("Submitting job")
        submitted = self.submitJob(jsonString)

        submitted = True

        if submitted == False:
            # TODO - How do we pass this error back to the calling SimPhoNY code?
            # TODO - Should there be a CUDS objects to hold error messages?
            logger.error("Job was not submitted successfully")
            return None

        logger.info("Job successfully submitted.")

        # Wait a little time for the request to process
        time.sleep(self.POLL_INTERVAL)

        # Request outputs
        outputs = self.requestOutputs()

        if(outputs == None):
            logger.error("Could not get job outputs (failed job?), returning None")
            return None

        logger.info("Job completed, returning JSON representation of output data")
        return outputs


    def submitJob(self, jsonString: str) -> bool:
        """Submits a job using a HTTP request with the input JSON string, stores
        resulting job ID returned by MoDS Agent.

        Arguments:
            jsonString (str) -- Input parameter data in raw JSON form

        Returns:
            True if a job was succesfully submitted
        """

        # Build the job submission URL
        url = self.buildSubmissionURL(jsonString)

        # Submit the request and get the response
        response = requests.get(url)

        # Check the HTTP return code
        if(response.status_code != 200):
            logger.error("HTTP request returns unexpected status code {response.status_code}")
            logger.error("Reason: {response.reason}")
            return False

        # Get the returned RAW text
        returnedRaw = response.text

        # Parse into JSON
        returnedJSON = json.loads(returnedRaw)

        # Get the generated job ID from the JSON
        self.jobID = returnedJSON["jobId"]
        logger.info(f"Job submitted successfully, resulting job ID is {self.jobID}")
        return True


    def requestOutputs(self)-> Optional[Dict]:
        """Sends a HTTP request asking for the results of the submitted job.
        If the job fails, None is returned. Note that this function will block
        until the job has executed on the remote machine.

        Returns:
            JSON object detailing job outputs (None in case of failure)
        """

        # Build the URL
        url = self.buildOutputURL()

        # Submit the request
        result = self.__getJobResults(url, 1)
        if(result == None):
            logger.error("Job was not completed on the remote HPC!")
            return None

        # Detect if the job has actually finished successfully
        if("message" in result):
            message = result["message"]

            if(message.find("error") >= 0):
                logger.error("Job finished with errors, no outputs received.")
                return None

        logger.info("Job finished successfully, output data received.")
        return result


    def buildSubmissionURL(self, jsonString: str) -> str:
        """Builds the submission URL for the input JSON string.

        Arguments:
            jsonString (str) -- Input parameter data in JSON form

        Returns:
            Full job submission URL
        """
        url = self.BASE_URL + self.SUBMISSION_URL_PART
        url += self.encodeURL(jsonString)
        return url


    def buildOutputURL(self) -> str:
        """Builds the request outputs URL for the current job ID.

        Arguments:
            jsonString (str) -- Input parameter data in JSON form

        Returns:
            Full output request URL
        """
        url = self.BASE_URL + self.OUTPUT_URL_PART

        # Build JSON from job ID
        jsonString = "{\"jobId\":\"" + str(self.jobID) + "\"}"

        url += self.encodeURL(jsonString)
        return url


    def encodeURL(self, string: str) -> str:
        """Encodes the input string into a valid URL

        Arguments:
            string (str) --- string to encode

        Returns:
            Valid URL
        """
        return urllib.parse.quote(string)


    def __getJobResults(self, url: str, attempt: int)-> Optional[Dict]:
        """Make a HTTP request to get the final results of the submitted job.
        Recurses until the request reports that the job is finished (or a
        maximum number of attempts is reached)

        Arguments:
            url (str)     -- Output request URL
            attempt (int) -- Current attempt index

        Returns:
            JSON object parsed from response (or None if failure occurs)
        """

        # Fail at is more than max attempts
        if(attempt >= self.MAX_ATTEMPTS):
            logger.warning("Maximum number of attempts reached, considering job a failure.")
            return None

        # Submit the request
        response = requests.get(url)

        # Check the HTTP return code
        if(response.status_code != 200):
            logger.error(f"HTTP request returns unexpected status code {response.status_code}")
            logger.error(f"Reason: {response.reason}")
            return None

        # Get the returned RAW text
        returnedRaw = response.text

        # Parse into JSON
        returnedJSON = json.loads(returnedRaw)

        # Detect if the job has actually finished successfully
        if("message" in returnedJSON):
            message = returnedJSON["message"]

            if((message.find("executing") >= 0) or (message.find("executed") >= 0)):
                logger.info(f"Job still running (attempt {attempt} of {self.MAX_ATTEMPTS})")

                # Wait
                time.sleep(self.POLL_INTERVAL)
                return self.__getJobResults(url, attempt + 1)

        else:
            return returnedJSON