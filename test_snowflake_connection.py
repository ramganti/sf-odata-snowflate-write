import snowflake.connector

# Snowflake connection details (replace with your actual values)
# account = "HAWQPMW-NCB25403"    
# user = "RAMGANTI2002"
# password = "DemoRgAccountForTest123"
# database = "DEMODB"

user='RG06052025'
password='DemoRgAccountForTest123'
account='EMWLIJW-YM14503'
# warehouse='COMPUTE_WH'
# schema='PUBLIC'
database='DEMODB'
role='ACCOUNTADMIN'



try:
    # Connect
    ctx = snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        database=database,
        role=role
    )
    
    cs = ctx.cursor()
    
    # Simple query
    cs.execute("SELECT * FROM COMMISSION_DATA LIMIT 10")
    rows = cs.fetchall()
    
    for row in rows:
        print(row)

except Exception as e:
    print(f"❌ Connection failed: {e}")

finally:
    try:
        cs.close()
        ctx.close()
    except:
        pass