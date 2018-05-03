# (ActiveDirectory)-[:Python]->(Neo4j)

Version: nr1 "First Make it work."

This script is for retrieving ActiveDirectory objects and insert these objects in a Neo4j Graph database to visualize there relationships based on groupmembership.

For this script I used Fedora 27, ActiveDirectory, a Domain account, Neo4j, Python.
This is the first version tested on a small ActiveDirectory.

To run the script on Linux you need to make it executable first with chmod +x {sriptname}.
Then and open the script with a texteditor and adjust the values of the fields with {} save the file. You can run it with ./{scriptname} if there are no errors, the Neo4j GraphDB is filled. Now you can go to the graph database with http://localhost:7474.




