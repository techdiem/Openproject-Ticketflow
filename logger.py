import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', 
                    filename='ticketflow.log', 
                    filemode='w', 
                    encoding='utf-8', 
                    level=logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.info("Initialized logging")
