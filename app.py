import os
from flask import Flask, request, jsonify, Response
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# --- Snowflake Configuration ---
# Pulls connection details securely from your .env file
SNOWFLAKE_CONFIG = {
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    'database': os.getenv('SNOWFLAKE_DATABASE'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA'),
    'role': os.getenv('SNOWFLAKE_ROLE')  # <-- ADD THIS LINE
}

# --- OData Metadata Endpoint ---
# Salesforce Connect MUST call this endpoint first to understand the data structure.
# This XML defines our 'CommissionRecord' entity.
@app.route('/odata/$metadata', methods=['GET'])
def get_metadata():
    """
    Provides the OData V4 metadata XML that describes the CommissionData entity.
    """
    metadata_xml = """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
    <edmx:DataServices>
        <Schema Namespace="Salesforce.POC" xmlns="http://docs.oasis-open.org/odata/ns/edm">
            <EntityType Name="CommissionRecord">
                <Key>
                    <PropertyRef Name="OpportunityID" />
                </Key>
                <Property Name="OpportunityID" Type="Edm.String" Nullable="false" />
                <Property Name="CommissionAmount" Type="Edm.Decimal" Scale="2" />
                <Property Name="Status" Type="Edm.String" />
                <Property Name="Needs_Review_Flag" Type="Edm.Boolean" />
                <Property Name="Review_Reason" Type="Edm.String" />
                <Property Name="LastModifiedDate" Type="Edm.DateTimeOffset" />
            </EntityType>
            <EntityContainer Name="DefaultContainer">
                <EntitySet Name="CommissionData" EntityType="Salesforce.POC.CommissionRecord" />
            </EntityContainer>
        </Schema>
    </edmx:DataServices>
</edmx:Edmx>"""
    return Response(metadata_xml, mimetype='application/xml')

# --- OData Service Document ---
# This endpoint lists all the available data collections (Entity Sets).
@app.route('/odata/', methods=['GET'])
def get_service_document():
    """
    Provides the OData service document listing available entity sets.
    """
    service_doc = {
        "@odata.context": f"{request.url_root}odata/$metadata",
        "value": [
            {"name": "CommissionData", "kind": "EntitySet", "url": "CommissionData"}
        ]
    }
    return jsonify(service_doc)


# --- OData Read/Query Endpoint (IMPROVED VERSION) ---
@app.route('/odata/CommissionData', methods=['GET'])
def get_commission_data():
    """
    Handles GET requests to read commission data.
    - If a $filter for OpportunityID is present, it fetches a single record.
    - Otherwise, it fetches all records for the list view.
    """
    odata_filter = request.args.get('$filter')
    results = []
    
    try:
        with snowflake.connector.connect(**SNOWFLAKE_CONFIG) as conn:
            with conn.cursor() as cur:
                # CASE 1: Handle request for a SINGLE record (for detail pages)
                if odata_filter and 'OpportunityID eq' in odata_filter:
                    opp_id = odata_filter.split("'")[1]
                    sql_query = "SELECT OpportunityID, CommissionAmount, Status, Needs_Review_Flag, Review_Reason, LastModifiedDate FROM COMMISSION_DATA WHERE OpportunityID = %s"
                    cur.execute(sql_query, (opp_id,))
                    # fetchone() gets a single result
                    records = cur.fetchall() 
                
                # CASE 2: Handle request for ALL records (for list views)
                else:
                    # For the POC, we will ignore $top, $orderby etc. and just return all records.
                    sql_query = "SELECT OpportunityID, CommissionAmount, Status, Needs_Review_Flag, Review_Reason, LastModifiedDate FROM COMMISSION_DATA"
                    cur.execute(sql_query)
                    # fetchall() gets all results
                    records = cur.fetchall()

                # Process all found records into a list
                for record in records:
                    results.append({
                        "OpportunityID": record[0],
                        "CommissionAmount": float(record[1]) if record[1] is not None else None,
                        "Status": record[2],
                        "Needs_Review_Flag": record[3],
                        "Review_Reason": record[4],
                        "LastModifiedDate": record[5].isoformat() if record[5] is not None else None
                    })

        # Format the final response in the required OData structure
        response_payload = {
            "@odata.context": f"{request.url_root}odata/$metadata#CommissionData",
            "value": results
        }
        return jsonify(response_payload)

    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

# --- OData Update Endpoint ---
@app.route("/odata/CommissionData('<key>')", methods=['POST'])
def update_commission_data(key):
    """
    Handles PATCH requests to update a single commission record.
    The 'key' is the OpportunityID from the URL.
    """
    try:
        update_data = request.get_json()   
        print('>>>update_data>>>>',update_data) 
        needs_review = update_data.get('Needs_Review_Flag')
        review_reason = update_data.get('Review_Reason')
        status = update_data.get('Status')
        commission_amount = update_data.get('CommissionAmount')


        with snowflake.connector.connect(**SNOWFLAKE_CONFIG) as conn:
            with conn.cursor() as cur:
                sql_update = """
                    UPDATE COMMISSION_DATA
                    SET Needs_Review_Flag = %s, Review_Reason = %s, Status = %s, CommissionAmount = %s, LastModifiedDate = CURRENT_TIMESTAMP()
                    WHERE OpportunityID = %s
                """
                cur.execute(sql_update, (needs_review, review_reason, status, commission_amount, key))

        # A successful OData PATCH should return a 204 No Content response
        return '', 204

    except Exception as e:
        print(f"Update Error: {e}")
        return jsonify({"error": "Failed to update record"}), 500

# This block allows you to run the app directly using "python app.py"
if __name__ == '__main__':
    # Use debug=True for development, which provides auto-reloading and helpful errors.
    # Remove debug=True for a production environment.
    app.run(debug=True, port=7001)