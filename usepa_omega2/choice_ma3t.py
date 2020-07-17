from vb2py.vbfunctions import *
from vb2py.vbdebug import *
import numpy as np

def PHEVT_Consumer():
    rootdir = 'C:/Users/KBolon/Documents/ma3t_python_version/'
    YearOnMarket = np.loadtxt(rootdir + 'tech_yearonmarket.csv', delimiter=',', skiprows=1, usecols=range(1,2))
    dBeta = np.loadtxt(rootdir + 'consumer_beta.csv', delimiter=',', skiprows=0, usecols=range(1,136))
    bDummyFlag = np.loadtxt(rootdir + 'tech_nestheterogeneity.csv', delimiter=',', skiprows=0, usecols=range(1,406))
    generalizedcost = np.loadtxt(rootdir + 'generalizedcosts.csv', delimiter=',', skiprows=1, usecols=range(1,47))

    dCost = vbObjectInitialize(objtype=Double)
    dEtoU = vbObjectInitialize(objtype=Double)
    dSumEtoU = vbObjectInitialize(objtype=Double)
    dProb = vbObjectInitialize(objtype=Double)
    iRealChoice = Integer()
    dBuyCost = Double()
    dBuyU = Double()
    dBuyEtoU = Double()
    dNoBuyEtoU = Double()
    iNestLayerNum = 5
    iNestPerNestNum = [5, 3, 3, 3, 3]
    iChoiceNum = [5, 15, 45, 135, 405]
    dExteremeHighPrice = 99999999
    iIndividualNum = [1]# Use a single aggregate consumer for now
    iGroupDimNum = 1 # Use a single aggregate consumer for now
    iStepNum = 2050 - 2005 + 1

    for iStepIndex in range(1, iStepNum):
        #Calculate choice probability of each technology by each consumer---objConsumer(iConsumer).ChoiceProb(iChoice)
        #Calcualte the sales of each choice -- objChoice(iChoice).DDSales

        dCost = vbObjectInitialize(((1, iNestLayerNum), (1, iChoiceNum[iNestLayerNum]),), Double)
        dEtoU = vbObjectInitialize(((1, iNestLayerNum), (1, iChoiceNum[iNestLayerNum]),), Double)
        dSumEtoU = vbObjectInitialize(((1, iNestLayerNum), (1, iChoiceNum[iNestLayerNum - 1]),), Double)
        dProb = vbObjectInitialize(((1, iNestLayerNum), (1, iChoiceNum[iNestLayerNum]),), Double)


        for iConsumer in range(1, 2): #iIndividualNum[iGroupDimNum - 1]):
            #1
            AssignValueToArray(dSumEtoU, 1, iNestLayerNum, 1, iChoiceNum[iNestLayerNum - 1], 0)
            iRealChoice = 1
            for iChoice in vbForRange(1, iChoiceNum[iNestLayerNum]):
                if bDummyFlag[iNestLayerNum, iChoice] == 0:
                    dCost[iNestLayerNum, iChoice] = dExteremeHighPrice
                    dEtoU[iNestLayerNum, iChoice] = 0
                else:
                    if YearOnMarket[iRealChoice] <= iStepIndex:
                        dCost[iNestLayerNum, iChoice] = generalizedcost[iRealChoice, iStepIndex]
                    else:
                        dCost[iNestLayerNum, iChoice] = dExteremeHighPrice
                    #calculate dCost(iNestLayerNum, i)
                    #function of dLamda, and attributes; form depends on attributes and parameters setting
                    iTemp = Int((iChoice - 1)  / iNestPerNestNum[iNestLayerNum]) + 1
                    dEtoU[iNestLayerNum, iChoice] = Exp(dBeta[iNestLayerNum, iTemp] * dCost[iNestLayerNum, iChoice])
                    #calculate dSumEtoU(iNestLayerNum, i)
                    dSumEtoU[iNestLayerNum, iTemp] = dSumEtoU[iNestLayerNum, iTemp] + dEtoU[iNestLayerNum, iChoice]
                    iRealChoice = iRealChoice + 1
            #calculate dProb(iNestLayerNum, i)
            for iChoice in vbForRange(1, iChoiceNum[iNestLayerNum]):
                iTemp = Int(( iChoice - 1 )  / iNestPerNestNum[iNestLayerNum]) + 1
                if bDummyFlag[iNestLayerNum, iChoice] == 0:
                    dProb[iNestLayerNum, iChoice] = 0
                elif bDummyFlag[iNestLayerNum, iChoice] == 100:
                    dProb[iNestLayerNum, iChoice] = 1
                elif dSumEtoU(iNestLayerNum, iTemp) == 0:
                    dTemp = 0
                    for iTemp2 in vbForRange(1, iNestPerNestNum[iNestLayerNum]):
                        dTemp = dTemp + bDummyFlag[iNestLayerNum, ( iTemp - 1 )  * iNestPerNestNum[iNestLayerNum] + iTemp2]
                    dProb[iNestLayerNum, iChoice] = 1 / dTemp / 11
                else:
                    dProb[iNestLayerNum, iChoice] = dEtoU(iNestLayerNum, iChoice) / dSumEtoU(iNestLayerNum, iTemp)
            for iLayer in vbForRange(( iNestLayerNum - 1 ) , 1, - 1):
                #2
                for iNest in vbForRange(1, iChoiceNum[iLayer]):
                    #3
                    if bDummyFlag[iLayer, iNest] == 0 or dSumEtoU[iLayer + 1, iNest] == 0:
                        dCost[iLayer, iNest] = dExteremeHighPrice
                        dEtoU[iLayer, iNest] = 0
                    else:
                        #calculate dCost(iLayer, iNest)
                        dCost[iLayer, iNest] = Log(dSumEtoU[iLayer + 1, iNest]) / dBeta[iLayer + 1, iNest]
                        #calculate dEtoU(iLayer, iNest)
                        iTemp = Int(( iNest - 1 )  / iNestPerNestNum[iLayer]) + 1
                        dEtoU[iLayer, iNest] = Exp(dBeta[iLayer, iTemp] * dCost[iLayer, iNest])
                        #calculate dSumEtoU(iNestLayerNum, i)
                        dSumEtoU[iLayer, iTemp] = dSumEtoU[iLayer, iTemp] + dEtoU[iLayer, iNest]
                    #3
                #calculate dProb(iLayer, iNest)
                for iNest in vbForRange(1, iChoiceNum[iLayer]):
                    iTemp = Int(( iNest - 1 )  / iNestPerNestNum[iLayer]) + 1
                    if bDummyFlag[iLayer, iNest] == 0:
                        dProb[iLayer, iNest] = 0
                    elif bDummyFlag[iLayer, iNest] == 100:
                        dProb[iLayer, iNest] = 1
                    elif dSumEtoU[iLayer, iTemp] == 0:
                        dTemp = 0
                        for iTemp2 in vbForRange(1, iNestPerNestNum[iLayer]):
                            dTemp = dTemp + bDummyFlag[iLayer, ( iTemp - 1 ) * iNestPerNestNum[iLayer] + iTemp2]
                        dProb[iLayer, iNest] = 1 / dTemp / 11
                    else:
                        dProb[iLayer, iNest] = dEtoU[iLayer, iNest] / dSumEtoU[iLayer, iTemp]
                #2
            #1
    np.savetxt(rootdir + 'dProb.csv', dProb, delimiter=',')

def AssignValueToArray(LcTargetArray, iLcRowL, iLcRowU, iLcColL, iLcColU, LcSourceArray):
    iLcRow = Integer()
    iLcCol = Integer()
    iLcDim = Integer()
    iLcDimS = Integer()

    ## ToDo: need to define the dimensions of the array

    # # check dimensionality of target array. If 2 dim, then iLcDim=2. If 1 dim, then iLcDim=1
    # # VB2PY (UntranslatedCode) On Error Resume Next
    # iLcDim = UBound(LcTargetArray, 2)
    # iLcDim = 2
    # if Err.Number == 9:
    #     iLcDim = 1
    # Err.Clear()
    # # VB2PY (UntranslatedCode) On Error GoTo 0
    # # check dimensionality of source array. If 2 dim, then iLcDimS=2. If 1 dim, then iLcDimS=1
    # # VB2PY (UntranslatedCode) On Error Resume Next
    # iLcDimS = UBound(LcSourceArray, 2)
    # iLcDimS = 2
    # if Err.Number == 9:
    #     iLcDimS = 1
    # Err.Clear()
    # # VB2PY (UntranslatedCode) On Error GoTo 0

    if IsArray(LcSourceArray):
        if iLcRowL == iLcRowU:
            if iLcDimS == 1:
                if iLcDim == 2:
                    for iLcCol in vbForRange(iLcColL, iLcColU):
                        LcTargetArray[iLcRowL, iLcCol] = LcSourceArray(iLcCol + 1 - iLcColL)
                else:
                    for iLcCol in vbForRange(iLcColL, iLcColU):
                        LcTargetArray[iLcCol] = LcSourceArray(iLcCol + 1 - iLcColL)
            else:
                if iLcDim == 2:
                    for iLcCol in vbForRange(iLcColL, iLcColU):
                        LcTargetArray[iLcRowL, iLcCol] = LcSourceArray(1, iLcCol + 1 - iLcColL)
                else:
                    for iLcCol in vbForRange(iLcColL, iLcColU):
                        LcTargetArray[iLcCol] = LcSourceArray(1, iLcCol + 1 - iLcColL)
        elif iLcColL == iLcColU:
            if iLcDim == 2:
                for iLcRow in vbForRange(iLcRowL, iLcRowU):
                    LcTargetArray[iLcRow, iLcColL] = LcSourceArray(iLcRow + 1 - iLcRowL)
            else:
                for iLcRow in vbForRange(iLcRowL, iLcRowU):
                    LcTargetArray[iLcRow] = LcSourceArray(iLcRow + 1 - iLcRowL)
        else:
            for iLcRow in vbForRange(iLcRowL, iLcRowU):
                for iLcCol in vbForRange(iLcColL, iLcColU):
                    LcTargetArray[iLcRow, iLcCol] = LcSourceArray(iLcRow + 1 - iLcRowL, iLcCol + 1 - iLcColL)
    else:
        if iLcRowL == iLcRowU and iLcDim == 1:
            for iLcCol in vbForRange(iLcColL, iLcColU):
                LcTargetArray[iLcCol] = LcSourceArray
        elif iLcColL == iLcColU and iLcDim == 1:
            for iLcRow in vbForRange(iLcRowL, iLcRowU):
                LcTargetArray[iLcRow] = LcSourceArray
        else:
            for iLcRow in vbForRange(iLcRowL, iLcRowU):
                for iLcCol in vbForRange(iLcColL, iLcColU):
                    LcTargetArray[iLcRow, iLcCol] = LcSourceArray

# main
PHEVT_Consumer()
