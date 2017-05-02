'''
The Chinese University of Hong Kong
CENG 3410 - Smart Hardware Design
Project: Smart Price Tags

Xbee Pricetag PC console
Author: Terry Tsang

v0.1.0 (2/5/2017)
'''

import Tkinter as tk
import tkMessageBox
import sqlite3
import serial
import struct
import json
#from xbee import XBee

dictPricetag = {}	# [addr64] = product_id
dictProduct = {}	# [product_id] = (product_disp_name, price, key_ProductList)
dictPricetagList = {}	# [key_AddrList] = addr64
dictProductList = {}	# [key_ProductList] = product_id
db = None	# SQLite object
cur = None	# db cursor

'''
Xbee related functions
'''
def connectCOM():
	global etyCOM
	
	COM = etyCOM.get()
	buad = svBaud.get()
	
	if not COM or not buad:
		return False
		
	try:
		ser = serial.Serial(COM, int(buad))
		return ser
	except:
		return False
		
	'''
	Custom function to construct XBee tx request frame
	'''
def buildTxFrame(addr64, frame_id=b'\x01', options=b'\x00', data = None):
	if len(addr64) != 16:
		return False
	frame = "7E".decode("hex")
	length = struct.pack("> h", len(data) + 15)	# Length field. len(data) must +1 to include tailing \x00
	frame += length
	payload = "\x10" + frame_id + addr64.decode("hex") + "\xFF\xFE" + "\x00" + options + data # plylaod
	checksum = 0
	for byte in payload:
		checksum += ord(byte)
	checksum &= 0xFF	# keep only last byte
	checksum = 0xFF - checksum
	frame += payload
	frame += struct.pack("> h", checksum)
	
	print "Frame: " + ' '.join(x.encode('hex') for x in frame)
	return frame
	
def buildProductInfoJSON(name, price):
	# price is currency integer
	#print json.dumps({"p_name": name, "price": float(price / 10.0)}, separators=(',', ':'))
	return json.dumps({"p_name": name, "price": float(price / 10.0)}, separators=(',', ':'))

def syncOneTag(addr64):
	global db, cur
	COM = connectCOM()
	
	# Error check
	if len(addr64) != 16:
		svStatusBar.set("Error: Invaild address!")
		return
	if not COM:
		svStatusBar.set("Error: Unable to connect to COM port!")
		tkMessageBox.showerror("Error", "Failed to connect to COM port!")
		return
		
	# Get product info
	cur.execute("SELECT COUNT(*), product.product_disp_name, product.price from pricetag, product WHERE addr64=? and (pricetag.product_id=product.product_id)", (addr64,))
	
	row = cur.fetchone()
	print row
	if row[0] != 1:	# No or more than 1 rows returned
		svStatusBar.set("Error: Product not found in database!")
		tkMessageBox.showerror("Error", "Product not found for pricetag " + addr64)
		return
	data = buildProductInfoJSON(row[1], row[2])
	
	# send frame to pricetag
	frame = buildTxFrame(addr64, data=data)
	COM.write(frame)
	COM.close()
	
		
def syncAllTag():
	global db, cur
	COM = connectCOM()
	print COM
	if not COM:
		svStatusBar.set("Error: Unable to connect Xbee device!")
		tkMessageBox.showerror("Error", "Failed to connect to COM port!")
		return
	#xbee = XBee(COM)
		
	svStatusBar.set("Synchronizing all pricetags...")
	
	# retrieve all pricetags
	cur.execute("SELECT addr64, product_disp_name, price FROM pricetag LEFT JOIN product ON product.product_id = pricetag.product_id")
	rows = cur.fetchall()
	print rows
	for row in rows:
		if not row[1]:
			# Set pricetags which have no product info
			frame = buildTxFrame(row[0], data=buildProductInfoJSON("Not Available", 0))
			COM.write(frame)
		else:
			# Set pricetags
			frame = buildTxFrame(row[0], data=buildProductInfoJSON(row[1], int(row[2])))
			COM.write(frame)
		# TODO: wait for transmit status frame
		
	svStatusBar.set("All pricetags have been synchronized!")
			
	COM.close()
	return

'''
Database related functions
'''
def refreshDevice():
	global db, cur, dictPricetag, dictPricetagList, listAddrList
	# clear all data in list first
	dictPricetagList = {}
	listAddrList.delete(0, "end")
	cur.execute("SELECT addr64, pricetag.product_id, product_disp_name FROM pricetag LEFT JOIN product ON pricetag.product_id = product.product_id ORDER BY addr64")
	rows = cur.fetchall()
	print "Device list:"
	for row in rows:
		print row
		dictPricetag[row[0]] = row[1]
		dictPricetagList[listAddrList.index("end")] = row[0]
		if row[1] == None:
			listAddrList.insert("end", row[0] + ": ")
		else:
			listAddrList.insert("end", row[0] + ": " + str(row[1]) + " " + row[2])
	
	print "\ndictPricetag:"
	print dictPricetag
	print "dictPricetagList:"
	print dictPricetagList
	return
	
def refreshProduct():
	global db, cur, dictProduct, dictProductList, listProductList
	# clear all data in list first
	dictProductList = {}
	listProductList.delete(0, "end")
	cur.execute("SELECT * FROM product ORDER BY product_id")
	rows = cur.fetchall()
	print "Product list:"
	for row in rows:
		print row
		dictProduct[row[0]] = (row[1], row[2], listProductList.index("end"))
		dictProductList[listProductList.index("end")] = row[0]
		listProductList.insert("end", str(row[0]) + ": " + row[1])
	
	print "\ndictProduct:"
	print dictProduct
	print "dictProductList:"
	print dictProductList
	return
	
def addDevice():
	global db, cur, listAddrList, etyAddr64
	addr64 = etyAddr64.get()
	
	# Error check
	if len(addr64) != 16:
		svStatusBar.set("Error: Please enter device's 64-bit address!")
		return
	
	# Insert record
	try:
		cur.execute("INSERT INTO pricetag VALUES (?, ?)", (addr64, None))
		db.commit()
		refreshDevice()
		svStatusBar.set("Device added: " + addr64)
	except sqlite3.IntegrityError:
		svStatusBar.set("Address already exist in database!")
		return
		
def delDevice():
	global db, listAddrList, etyAddr64
	addr64 = etyAddr64.get()
	
	# Error check
	if len(addr64) != 16:
		svStatusBar.set("Error: Please select an existing pricetag!")
		return
	
	# Delete record
	cur.execute("DELETE FROM pricetag WHERE addr64 = ?", (addr64,))
	if cur.rowcount == 0:
		svStatusBar.set("Error: Address not found!")
		return
	else:
		db.commit()
		svStatusBar.set("Pricetag " + addr64 + " removed!")
		svAddr64.set("")
		refreshDevice()
		return
		
def addProduct():
	global db, cur, etyProductName, etyProductPrice
	id = etyProductID.get()
	name = etyProductName.get()
	price = etyProductPrice.get()
	
	# Validations
	if not id or not name or not price:
		svStatusBar.set("Error: Product ID, name or price is not set!")
		return
	if not id.isdigit() or int(id) > 99999:
		svStatusBar.set("Error: Product ID should be a 5-digit number!")
		return
	if len(name) > 21:
		svStatusBar.set("Error: Product name is too long!")
		return
	if not price.replace('.', '', 1).isdigit() or float(price) >= 10000:
		svStatusBar.set("Error: Price should be a number < 10000!")
		return
		
	id_int = int(id)
	price = int(float(price) * 10)	# convert price to currency (integer based)
	
	# add record
	try:
		cur.execute("INSERT INTO product VALUES (?, ?, ?)", (id_int, name, price))
		db.commit()
		svStatusBar.set("Product " + id + " added to database!")
		refreshProduct()
		return
	except sqlite3.IntegrityError:
		svStatusBar.set("Product ID already exist in database!")
		return
		
def delProduct():
	global db, cur, etyProductID
	id = etyProductID.get()
	
	# Validations
	if not id:
		svStatusBar.set("Error: Product ID is not set!")
		return
	if not id.isdigit() or int(id) > 99999:
		svStatusBar.set("Error: Product ID should be a 5-digit number!")
		return
		
	id_int = int(id)
	
	# mark affected devices
	addr64List = []
	cur.execute("SELECT addr64 FROM pricetag WHERE product_id = ?", (id_int,))
	rows = cur.fetchall()
	for row in rows:
		addr64List.append(row[0])
	print "Affected deviced: "
	print addr64List
	
	# delete record
	cur.execute("DELETE FROM product WHERE product_id = ?", (id_int,))
	if cur.rowcount == 0:
		svStatusBar.set("Error: Product ID not found in database!")
		return
	else:
		db.commit()
		svStatusBar.set("Product " + id + " removed from database!")
		svProductID.set("")
		svProductName.set("")
		svProductPrice.set("")
		msg = 'The following pricetags might be affected:\n' + ''.join(x + '\n' for x in addr64List)
		tkMessageBox.showinfo("Product Removed", msg)
		
		# assume product_id in pricetag table are removed
		
		# update affected devices
		for addr64 in addr64List:
			syncOneTag(addr64)
			
		# refresh lists
		refreshProduct()
		refreshDevice()
		return
	
def updateProduct():
	global db, cur, etyProductName, etyProductPrice
	id = etyProductID.get()
	name = etyProductName.get()
	price = etyProductPrice.get()
	
	# Validations
	if not id or not name or not price:
		svStatusBar.set("Error: Product ID, name or price is not set!")
		return
	if not id.isdigit() or int(id) > 99999:
		svStatusBar.set("Error: Product ID should be a 5-digit number!")
		return
	if len(name) > 21:
		svStatusBar.set("Error: Product name is too long!")
		return
	if not price.replace('.', '', 1).isdigit() or float(price) >= 10000:
		svStatusBar.set("Error: Price should be a number < 10000!")
		return
		
	id_int = int(id)
	price = int(float(price) * 10)	# convert price to currency (integer based)
	
	# mark affected devices
	addr64List = []
	cur.execute("SELECT addr64 FROM pricetag WHERE product_id = ?", (id_int,))
	rows = cur.fetchall()
	for row in rows:
		addr64List.append(row[0])
	print "Affected deviced: "
	print addr64List
	
	# update record
	cur.execute("Update product SET product_id=?, product_disp_name=?, price=? WHERE product_id = ?", (id_int, name, price, id_int))
	if cur.rowcount == 0:
		svStatusBar.set("Error: Product ID not found in database!")
		return
	else:
		db.commit()
		svStatusBar.set("Product " + id + " updated!")
		msg = 'The following pricetags might be affected:\n' + ''.join(x + '\n' for x in addr64List)
		tkMessageBox.showinfo("Product Update", msg)
		
		# assume product_id in pricetag table are removed
		
		# TODO: update affected devices
		for addr64 in addr64List:
			syncOneTag(addr64)
		
		# refresh lists
		refreshProduct()
		refreshDevice()
		return
		
def linkDeviceProduct():
	global db, cur, etyProductID, etyAddr64
	
	addr64 = etyAddr64.get()
	id = etyProductID.get()
	
	# Validations
	if len(addr64) != 16:
		svStatusBar.set("Error: Please select an existing pricetag!")
		return
	if not id:
		svStatusBar.sret("Error: Please select an existing product!")
		return
	if not id.isdigit() or int(id) > 99999:
		svStatusBar.set("Error: Product ID should be a 5-digit number!")
		return
		
	id_int = int(id)
	
	# update record
	cur.execute("UPDATE pricetag SET product_id=? WHERE addr64=?", (id_int, addr64))
	if cur.rowcount == 0:
		svStatusBar.set("Error: Pricetag's address not found in database!")
		return
	else:
		db.commit()
		svStatusBar.set("Pricetag " + addr64 + " linked to product " + id + " successfully!")
		
		# sync pricetag
		syncOneTag(addr64)
			
		# refresh device list
		refreshDevice()
		return
		
def updateAllPrice(factor):
	global db, cur
	
	cur.execute("UPDATE product SET  price = ROUND(price * %f, 0)" % factor)
	syncAllTag()
	return

'''
GUI Callback functions
'''
def selAddrList(evt):
	global dictPricetagList, dictProduct, svAddr64, listProductList
	w = evt.widget	# get widget who triggered the callback
	index = int(w.curselection()[0])
	print "Device list index = " + str(index)
	addr64 = dictPricetagList[index]
	#print "index=" + str(index)
	#print dictPricetagList
	
	# set text on pricetag editor
	svAddr64.set(addr64)
	
	# focus to associated product
	listProductList.selection_clear(0, "end")
	if not dictProduct.has_key(dictPricetag[addr64]):
		svStatusBar.set("Warning: This pricetag has no linkage to any product!")
		return
	product_index = dictProduct[dictPricetag[addr64]][2]
	print "Device assoicated to list index: " + str(product_index)
	listProductList.selection_set(product_index)
	listProductList.event_generate("<<ListboxSelect>>")	# Trigger the callback
	return
	
def selProductList(evt):
	global dictProduct, dictProductList, svProductName, svProductPrice
	w = evt.widget	# get widget who triggered the callback
	index = int(w.curselection()[0])
	print "Product list index = " + str(index)
	svProductID.set(dictProductList[index])
	svProductName.set(dictProduct[dictProductList[index]][0])	# set product name
	svProductPrice.set(str(dictProduct[dictProductList[index]][1] / 10.0))	# set price with conversion
	print w.curselection()
	svStatusBar.set("")
	return
	
def cbSyncOneTag():
	global etyAddr64
	
	addr64 = etyAddr64.get()
	
	# Error check
	if len(addr64) != 16:
		svStatusBar.set("Error: Please select an existing pricetag!")
		return
	
	syncOneTag(addr64)
	return
	
def cbIncreasePrices():
	updateAllPrice(1.1)

def cbDecreasePrices():
	updateAllPrice(0.9)

'''
GUI setup
'''
root = tk.Tk()
root.resizable(0, 0)
root.title("CENG3410 Pricetag Console")

# 1. Pricetag editor
lbfmPtEditor = tk.LabelFrame(root, text="Pricetag Editor", padx=5, pady=5)
lbfmPtEditor.grid(row=0)

# 1.1 Device list
lbAddrList = tk.Label(lbfmPtEditor, text="Pricetag List:")
lbAddrList.pack(anchor="w")
listAddrList = tk.Listbox(lbfmPtEditor, width=70, exportselection=0)
listAddrList.pack(anchor="w")
listAddrList.bind("<<ListboxSelect>>", selAddrList)
	# TODO: Add scrollbar

# 1.2 Device info
lbAddr64 = tk.Label(lbfmPtEditor, text="64-bit address:")
lbAddr64.pack(anchor="w", side="left");
svAddr64 = tk.StringVar()
etyAddr64 = tk.Entry(lbfmPtEditor, textvariable=svAddr64, width=20)
etyAddr64.pack(anchor="w", side="left")

# 1.3 Add/ Delete device
btnAddDevice = tk.Button(lbfmPtEditor, text="Add pricetag", command=addDevice)
btnAddDevice.pack(side="left")
btnDelDevice = tk.Button(lbfmPtEditor, text="Remove pricetag", command=delDevice)
btnDelDevice.pack(side="left")

# 2. Product editor
fmProductEditor = tk.LabelFrame(root, text="Product Editor", padx=5, pady=5)
fmProductEditor.grid(row=1, sticky="w")

# 2.1 Product list
lbProductList = tk.Label(fmProductEditor, text="Product List:")
lbProductList.grid(row=0, sticky="w")
listProductList = tk.Listbox(fmProductEditor, width=70, exportselection=0)
listProductList.grid(row=1, columnspan=4, sticky="w")
listProductList.bind("<<ListboxSelect>>", selProductList)
	# TODO: Add scrollbar

# 2.2 Item's info
fmProductInfo = tk.Frame(fmProductEditor)
fmProductInfo.grid(row=2, column=0, sticky="w")
lbProductID = tk.Label(fmProductInfo, text="Product ID:")
lbProductID.pack(side="left")
svProductID = tk.StringVar()
etyProductID = tk.Entry(fmProductInfo, textvariable=svProductID, width=5)
etyProductID.pack(side="left")
lbProductName = tk.Label(fmProductInfo, text="Product Name:")
lbProductName.pack(side="left")
svProductName = tk.StringVar()
etyProductName = tk.Entry(fmProductInfo, textvariable=svProductName, width=25)
etyProductName.pack(side="left")
lbProductPrice = tk.Label(fmProductInfo, text="Price: $")
lbProductPrice.pack(side="left")
svProductPrice = tk.StringVar()
etyProductPrice = tk.Entry(fmProductInfo, textvariable=svProductPrice, width=10)
etyProductPrice.pack(side="left")

# 2.3 Controls for product edit
fmProductCtrl = tk.Frame(fmProductEditor)
fmProductCtrl.grid(row=3, column=0, sticky="w")
btnAddProduct = tk.Button(fmProductCtrl, text="Add product", command=addProduct)
btnAddProduct.pack(side="left")
btnRemoveProduct = tk.Button(fmProductCtrl, text="Remove product", command=delProduct)
btnRemoveProduct.pack(side="left")
btnUpdateProduct = tk.Button(fmProductCtrl, text="Update product", command=updateProduct)
btnUpdateProduct.pack(side="left")

# 3. Controls for pricetag editor
fmControls = tk.Frame(root)
fmControls.grid(row=0, column=1, rowspan=2)
btnLinkTag = tk.Button(fmControls, width=12, text="Link pricetag\nto selected\nproduct", command=linkDeviceProduct)
btnLinkTag.pack()
btnSyncTag = tk.Button(fmControls, width=12, text="Sync selected\npricetag", command=cbSyncOneTag)
btnSyncTag.pack()
btnSyncAllTag = tk.Button(fmControls, width=12,text="Sync ALL\npricetags", command=syncAllTag)
btnSyncAllTag.pack()
btnIncreaseAll = tk.Button(fmControls, width=12,text="Increase ALL\nprice by 10%", command=cbIncreasePrices)
btnIncreaseAll.pack()
btnDecreaseAll = tk.Button(fmControls, width=12,text="Decrease ALL\nprice by 10%", command=cbDecreasePrices)
btnDecreaseAll.pack()
lbCOM = tk.Label(fmControls, text="COM port:")
lbCOM.pack(anchor="w")
etyCOM = tk.Entry(fmControls, width=12)
etyCOM.pack()
svBaud = tk.StringVar()
svBaud.set(9600)
lbBaud = tk.Label(fmControls, text="Buad rate:")
lbBaud.pack(anchor="w")
omBaud = tk.OptionMenu(fmControls, svBaud, 9600, 19200, 38400, 57600, 115200)
omBaud.pack(anchor="w")

# 4. Status bar
svStatusBar = tk.StringVar()
lbStatusBar = tk.Label(root,textvariable = svStatusBar)
lbStatusBar.grid(row=2, rowspan=2, sticky="w")

''' 
Main
'''
# Load database
svStatusBar.set("Loading database...")
db = sqlite3.connect("pricetag.db")
with db:
	cur = db.cursor()
	db.execute("PRAGMA foreign_keys = ON")	# support for foreign keys
	refreshDevice()
	refreshProduct()
	svStatusBar.set("Database loaded!")
	
	# display window
	root.mainloop()
	