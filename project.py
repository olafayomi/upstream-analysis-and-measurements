import numpy as np
print("To input matrix press 1")
request= "1 Addition\n 2 Subtraction\n 3 Scalar multiplication\n 4 Multiplication\n 5 Transpose\n 6 Determinant"
choice= input("")
print("Numbers inputted are arranged horizontally to form the matric")

if choice == "1":
	call= input("number of matrix (max 3):")
	if call == "1":
		rows= int(input("enter number of rows:"))
		columns= int(input("enter number of columns:"))
		matrix= [[int(input())for c in range(columns)]for r in range(rows)]
		hmm = np.array(matrix)
		print(request)
		process= input("")
		if process == "1":
			print("Kindly input an extra matric")
			rows= int(input("enter number of rows:"))
			columns= int(input("enter number of columns:"))
			ark= [[int(input())for c in range(columns)]for r in range(rows)]
			jae= np.array(ark)
			try:
				sum= jae + hmm
				print(sum)
			except ValueError:
				print("Invalid sum")
		elif process == "2":
			print("Kindly input an extra matric")
			rows= int(input("enter number of rows:"))
			columns= int(input("enter number of columns:"))
			ark= [[int(input())for c in range(columns)]for r in range(rows)]
			jae= np.array(ark)
			try:
				minus= hmm - jae
				print(minus)
			except ValueError:
				print("Invalid subtraction")
		elif process == "3":
			y= input("")
			way= int(y)*hmm
			print(way)
		elif process == "4":
			print("Kindly input an extra matric")
			rows= int(input("enter number of rows:"))
			columns= int(input("enter number of columns:"))
			ark= [[int(input())for c in range(columns)]for r in range(rows)]
			jae= np.array(ark)
			if columns == rows:
				multiresult = [[sum(hmm * jae for hmm, jae in zip(hmmrow, jaecol))
		      		for jaecol in zip(*hmm)]
 			  		for hmmrow in hmm]
				print("The multiplication result of the matrix is:")
				for res in multiresult:
					print(res)
			else:
				print("Multiplication not possible")
		elif process == "5":
			result= [[hmm[j][i] for j in range (len(hmm))] for i in range (len(hmm[0]))]
			

			for r in result:
				print(r)
		elif process == "6":
			if rows == columns:
				det = np.linalg.det(hmm)
				print("\n Determinant of given matrix:")
				print(int(det))
			else:
				print("Error")
			
		else:
			print("Error")
			

		
	elif call == "2":
		rows= int(input("enter number of rows:"))
		columns= int(input("enter number of columns:"))
		matrix= [[int(input())for c in range(columns)]for r in range(rows)]
		hmm = np.array(matrix)
		rows= int(input("enter number of rows:"))
		columns= int(input("enter number of columns:"))
		matrix_1= [[int(input())for c in range(columns)]for r in range(rows)]
		yo = np.array(matrix_1)
		print(request)
		pro= input("")
		if pro == "1":
			try:
				sum= yo + hmm
				print(sum)
			except ValueError:
				print("Invalid sum")
		elif pro == "2":
			try:
				minus= hmm- yo
				print(minus)
			except ValueError:
				print("Invalid subtraction")
		elif pro == "3":
			y= input("")
			way= int(y)*hmm
			stups= int(y)*yo
			print(way,"\n\n\n", stups)
		elif pro == "4":
			if columns == rows:
				multiresult = [[sum(hmm * yo for hmm, yo in zip(hmmrow, yocol))
		      		for yocol in zip(*hmm)]
 			  		for hmmrow in hmm]
				print("The multiplication result of the matrix is:")
				for res in multiresult:
					print(res)
			else:
				print("Multiplication not possible")
		elif pro == "5":
			result= [[hmm[j][i] for j in range (len(hmm))] for i in range (len(hmm[0]))]
			result_2= [[yo[j][i] for j in range (len(yo))] for i in range (len(yo[0]))]


			for r in result:
				print(r)
			for r in result_2:
				print( r)
		elif pro == "6":
			if rows == columns:
				det = np.linalg.det(hmm)
				print("\n Determinant of the first matrix:")
				print(int(det))

				det = np.linalg.det(yo)
				print("\n Determinant of the second matrix:")
				print(int(det))
				
			else:
				print("Error")
		else:
			print("Error")
		
	elif call == "3":
		rows= int(input("enter number of rows:"))
		columns= int(input("enter number of columns:"))
		matrix= [[int(input())for c in range(columns)]for r in range(rows)]
		hmm = np.array(matrix)
		rows= int(input("enter number of rows:"))
		columns= int(input("enter number of columns:"))
		matrix_1= [[int(input())for c in range(columns)]for r in range(rows)]
		yo = np.array(matrix_1)
		rows= int(input("enter number of rows:"))
		columns= int(input("enter number of columns:"))
		matrix_2= [[int(input())for c in range(columns)]for r in range(rows)]
		load = np.array(matrix_2)
		print(request)
		nom= input("")
		if nom == "1":
			try:
				sum = hmm + yo
				print(sum)
			except ValueError:
				print("Invalid sum")
			try:
				sum_1 = hmm + load
				print("\n",sum_1)
			except ValueError:
				print("Invalid sum")
			try:
				sum_2 = yo + load
				print("\n",sum_2)
			except ValueError:
				print("Invalid sum")
		elif nom == "2":
			try:
				minus = hmm - yo
				print(minus)
			except ValueError:
				print("Invalid subtraction")
			try:
				minus_1 = hmm - load
				print("\n",minus_1)
			except ValueError:
				print("Invalid subtraction")
			try:
				minus_2 = yo -load
				print("\n",minus_2)
			except ValueError:
				print("Invalid subtraction")
				
		elif nom == "3":
			y= input("")
			way= int(y)*hmm
			stups= int(y)*yo
			yup= int(y)*load
			print(way,"\n\n", stups,"\n\n",yup)
		elif nom == "4":
			if columns == rows:
				multiresult = [[sum(hmm * yo for hmm, yo in zip(hmmrow, yocol))
		      		for yocol in zip(*hmm)]
 			  		for hmmrow in hmm]
				print("The multiplication result of the matrix is:")
				for res in multiresult:
					print(res)
				multiresult = [[sum(hmm * load for hmm, load in zip(hmmrow, loadcol))
		      		for loadcol in zip(*hmm)]
 			  		for hmmrow in hmm]
				print("The multiplication result of the matrix is:")
				for res in multiresult:
					print(res)
				multiresult = [[sum(load * yo for load, yo in zip(loadrow, yocol))
		      		for yocol in zip(*load)]
 			  		for loadrow in load]
				print("The multiplication result of the matrix is:")
				for res in multiresult:
					print(res)
			else:
				print("Multiplication not possible")
		elif nom == "5":
			result= [[hmm[j][i] for j in range (len(hmm))] for i in range (len(hmm[0]))]
			result_2= [[yo[j][i] for j in range (len(yo))] for i in range (len(yo[0]))]
			result_3= [[load[j][i] for j in range (len(load))] for i in range(len(load[0]))]

			for r in result:
				print(r)
			for r in result_2:
				print( r)
			for r in result_3:
				print(r)
		elif nom == "6":
			if rows == columns:
				det = np.linalg.det(hmm)
				print("\n Determinant of the first matrix:")
				print(int(det))

				det = np.linalg.det(yo)
				print("\n Determinant of the second matrix:")
				print(int(det))

				det = np.linalg.det(load)
				print("\n Determinant of the third matrix:")
				print(int(det))
			else:
				print("Error")
		
		else:
			print("Error")
	else:
		print("Error")
		
else:
	print("Error")	

