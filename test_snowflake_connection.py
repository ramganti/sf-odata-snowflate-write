import snowflake.connector

user='RG06052025'
password='*****' # update password
account='XXXXX-XXXXX'
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
