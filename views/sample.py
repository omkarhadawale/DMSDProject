from flask import Blueprint, redirect, request, render_template, url_for, flash
from sql.db import DB
import pyodbc
import pandas as pd
from auth.forms import BorrowSubmit, ReaderId, SearchDocument
# import pandas as pd
sample = Blueprint('sample', __name__, url_prefix='/sample')


@sample.route('/add', methods=['GET', 'POST'])
def add():
    k = request.form.get("key", None)
    v = request.form.get("value", None)
    if k and v:
        try:
            result = DB.insertOne(
                "INSERT INTO IS601_Sample (name, val) VALUES(%s, %s)", k, v)
            if result.status:
                flash("Created Record", "success")
        except Exception as e:
            # TODO make this user-friendly
            flash(e, "danger")

    return render_template("add_sample.html")

@sample.route('/list', methods=['GET','POST'])
def list():
    RID = request.args.get("RID")
    READERNAME = request.args.get("READERNAME")
    form = SearchDocument()
    rows = None
    if form.validate_on_submit():
        value = form.value.data
        column = form.column.data
        limit = form.limit.data
        if len(limit)==0:
            limit = 10
        conn_str = (r'DRIVER={SQL Server};'r'SERVER=Omkar;'r'DATABASE=OPR;'r'Trusted_Connection=yes;')
        cnxn = pyodbc.connect(conn_str)
        print("connection established")
        # cursor = cnxn.cursor()
        try:
            data = pd.read_sql(f"SELECT TOP {limit} D.DOCID, D.TITLE, P.PUBNAME FROM DOCUMENT AS D, PUBLISHER AS P WHERE P.PUBLISHERID=D.PUBLISHERID AND {column} LIKE '%{value}%' ", cnxn)
            rows = data.to_dict('records')
        except Exception as e:
            flash(f"{str(e)}","danger")
            flash("Their was error retriving","warning")
    else:
        conn_str = (r'DRIVER={SQL Server};'r'SERVER=Omkar;'r'DATABASE=OPR;'r'Trusted_Connection=yes;')
        cnxn = pyodbc.connect(conn_str)
        print("connection established")
        # cursor = cnxn.cursor()
        try:
            data = pd.read_sql(f"SELECT TOP 10 D.DOCID, D.TITLE, P.PUBNAME FROM DOCUMENT AS D, PUBLISHER AS P WHERE P.PUBLISHERID=D.PUBLISHERID", cnxn)
            rows = data.to_dict('records')
        except Exception as e:
            flash(f"{str(e)}","danger")
            flash("Their was error retriving","warning")
    
    return render_template("document_list.html",form=form, resp=rows,RID=RID,READERNAME=READERNAME)


@sample.route('/checkout', methods=['GET'])
def checkout():
    DOCID = request.args.get("DOCID")
    
    
    
    flash("Book borrowed","success")
    return redirect(url_for("sample.list"))

@sample.route('/return', methods=['GET'])
def returns():
    RID = request.args.get("RID")
    READERNAME = request.args.get("READERNAME")
    DOCID = request.args.get("DOCID")
    COPYNO = request.args.get("COPYNO")
    BID = request.args.get("BID")
    if DOCID!=None and COPYNO!=None and BID!=None:
        conn_str = (r'DRIVER={SQL Server};'r'SERVER=Omkar;'r'DATABASE=OPR;'r'Trusted_Connection=yes;')
        cnxn = pyodbc.connect(conn_str)
        print("connection established")
        # cursor = cnxn.cursor()
        try:
            cursor = cnxn.cursor()
            cursor.execute(f"UPDATE BORROWING SET RDTIME=GETDATE() WHERE BOR_NO IN (SELECT BOR_NO FROM BORROWS WHERE DOCID='{DOCID}' AND COPYNO='{COPYNO}' AND BID='{BID}')")
            cursor.commit()
            flash("Book returned successfully","success")
            return redirect(url_for("sample.returns",RID=RID,READERNAME=READERNAME))
        except Exception as e:
            flash(f"{str(e)}","danger")
            flash("Their was error Returning book","warning")    

    conn_str = (r'DRIVER={SQL Server};'r'SERVER=Omkar;'r'DATABASE=OPR;'r'Trusted_Connection=yes;')
    cnxn = pyodbc.connect(conn_str)
    print("connection established")
    # cursor = cnxn.cursor()
    try:
        data = pd.read_sql(f"SELECT D.DOCID, D.TITLE , B.BID, B.COPYNO FROM BORROWS B, BORROWING BB,DOCUMENT D WHERE B.RID='{RID}' AND B.BOR_NO=BB.BOR_NO AND D.DOCID=B.DOCID AND BB.RDTIME IS NULL", cnxn)
        rows = data.to_dict('records')
    except Exception as e:
        flash(f"{str(e)}","danger")
        flash("Their was error retriving","warning")
    
    return render_template("borrowList.html", resp=rows,RID=RID,READERNAME=READERNAME)



    # flash("Book returned","success")    
    # return redirect(url_for("sample.list"))






@sample.route('/reserve', methods=['GET'])
def reserve():
    RID = request.args.get("DOCID")
    flash("Book reserved","success")
    return redirect(url_for("sample.list"))







@sample.route('/ReaderID', methods=['GET','POST'])
def ReaderID():
    form = ReaderId()
    form1 = BorrowSubmit()
    if form.validate_on_submit():
        RID = form.RID.data
        conn_str = (
        r'DRIVER={SQL Server};'
        r'SERVER=Omkar;'
        r'DATABASE=OPR;'
        r'Trusted_Connection=yes;')
        cnxn = pyodbc.connect(conn_str)
        print("connection established")
        try:
            data = pd.read_sql(f"SELECT * FROM READER WHERE RID='{RID}'", cnxn)
            data = data.to_dict('records')
            if len(data)>0:
                return redirect(url_for("sample.list",RID=RID,READERNAME=data[0]['RNAME'])) 
            else:
                flash("Invalid ReaderID","warning")    
        except Exception as e:
            flash(f"Error{str(e)}","danger")
    if form1.validate_on_submit():
        RID1 = form1.RID1.data
        conn_str = (
        r'DRIVER={SQL Server};'
        r'SERVER=Omkar;'
        r'DATABASE=OPR;'
        r'Trusted_Connection=yes;')
        cnxn = pyodbc.connect(conn_str)
        print("connection established")
        try:
            data1 = pd.read_sql(f"SELECT * FROM READER WHERE RID='{RID1}'", cnxn)
            data1 = data1.to_dict('records')
            if len(data1)>0:
                return redirect(url_for("sample.returns",RID=RID1,READERNAME=data1[0]['RNAME'])) 
            else:
                flash("Invalid ReaderID","warning")    
        except Exception as e:
            flash(f"Error{str(e)}","danger")        

            
    return render_template("getReaderID.html",form=form,form1=form1)   



@sample.route("/edit", methods=["GET", "POST"])
def edit():
    id = request.args.get("id")
    row = None
    if id is None:
        flash("ID is missing", "danger")
        return redirect("sample.list")
    else:
        if request.method == "POST" and request.form.get("value"):
            val = request.form.get("value")
            try:
                result = DB.update("UPDATE IS601_Sample SET val = %s WHERE id = %s", val, id)
                if result.status:
                    flash("Updated record", "success")
            except Exception as e:
                # TODO make this user-friendly
                flash(e, "danger")
        try:
            result = DB.selectOne("SELECT name, val FROM IS601_Sample WHERE id = %s", id)
            if result.status:
                row = result.row
        except Exception as e:
            # TODO make this user-friendly
            flash(e, "danger")
    return render_template("edit_sample.html", row=row)

@sample.route("/delete", methods=["GET"])
def delete():
    id = request.args.get("id")
    # make a mutable dict
    args = {**request.args}
    if id:
        try:
            result = DB.delete("DELETE FROM IS601_Sample WHERE id = %s", id)
            if result.status:
                flash("Deleted record", "success")
        except Exception as e:
            # TODO make this user-friendly
            flash(e, "danger")
        # TODO pass along feedback

        # remove the id args since we don't need it in the list route
        # but we want to persist the other query args
        del args["id"]
    return redirect(url_for("sample.list", **args))