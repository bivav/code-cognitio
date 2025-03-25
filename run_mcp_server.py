from mcp.server.fastmcp import FastMCP, Context
import logging
from typing import Dict, List, Any, Optional
from src.core.operations import CodeCognitioOperations

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("mcp_server.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Create an MCP server instance
mcp = FastMCP("CodeCognitio")

# Initialize operations
operations = CodeCognitioOperations()


@mcp.tool()
def search_code(
    query: str,
    top_k: int = 5,
    content_filter: Optional[str] = None,
    min_score: float = 0.0,
    type_filter: Optional[str] = None,
    param_type: Optional[str] = None,
    param_name: Optional[str] = None,
    return_type: Optional[str] = None,
    ctx: Context = None,
) -> List[Dict[str, Any]]:
    """
    Search the code repository using semantic search.

    Args:
        query: The search query
        top_k: Number of results to return
        content_filter: Filter results by content type (code/documentation)
        min_score: Minimum similarity score
        type_filter: Filter by Python type (function/class/method/module)
        param_type: Filter by parameter type
        param_name: Filter by parameter name
        return_type: Filter by return type
        ctx: MCP context for progress reporting

    Returns:
        List of search results with similarity scores
    """
    logger.info(f"Received search request - query: {query}, top_k: {top_k}")

    if ctx:
        ctx.info(f"Searching for: {query}")

    try:
        results = operations.search(
            query=query,
            top_k=top_k,
            content_filter=content_filter,
            min_score=min_score,
            type_filter=type_filter,
            param_type=param_type,
            param_name=param_name,
            return_type=return_type,
        )

        logger.info(f"Search completed - found {len(results)} results")
        if ctx:
            ctx.info(f"Found {len(results)} matching results")

        return results

    except Exception as e:
        error_msg = f"Error during search: {str(e)}"
        logger.error(error_msg)
        if ctx:
            ctx.error(error_msg)
        raise


if __name__ == "__main__":
    logger.info("Starting CodeCognitio MCP Server...")
    try:
        # Check index status before starting
        status = operations.get_index_status()
        logger.info(f"Index status: {status['status']}")
        if status["status"] != "ready":
            logger.warning("Search index is not ready. Please build the index first.")

        # Run the server
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        raise
