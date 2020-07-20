import numpy as np
import math

def PHEVT_Consumer():
    rootdir = 'C:/Users/KBolon/Documents/ma3t_python_version/'
    YearOnMarket = np.loadtxt(rootdir + 'tech_yearonmarket.csv', delimiter=',', skiprows=0, usecols=range(1,2))
    dBeta = np.loadtxt(rootdir + 'consumer_beta.csv', delimiter=',', skiprows=0, usecols=range(1,136))
    bDummyFlag = np.loadtxt(rootdir + 'tech_nestheterogeneity.csv', delimiter=',', skiprows=0, usecols=range(1,406))
    generalizedcost = np.loadtxt(rootdir + 'generalizedcosts.csv', delimiter=',', skiprows=1, usecols=range(1,47))
    iNestLayerNum = 5
    pyidxNestLayerNum = iNestLayerNum - 1
    iNestPerNestNum = [5, 3, 3, 3, 3]
    iChoiceNum = [5, 15, 45, 135, 405]
    dExteremeHighPrice = 99999999
    iIndividualNum = [1]# Use a single aggregate consumer for now
    iGroupDimNum = 1 # Use a single aggregate consumer for now
    iStepNum = 2050 - 2005 + 1

    for iStepIndex in range(1, iStepNum):
        #Calculate choice probability of each technology by each consumer---objConsumer(iConsumer).ChoiceProb(iChoice)
        dCost = np.empty([iNestLayerNum, iChoiceNum[pyidxNestLayerNum]])
        dEtoU = np.empty([iNestLayerNum, iChoiceNum[pyidxNestLayerNum]])
        dSumEtoU = np.empty([iNestLayerNum, iChoiceNum[pyidxNestLayerNum] - 1])
        dProb = np.empty([iNestLayerNum, iChoiceNum[pyidxNestLayerNum]])

        for iConsumer in range(0, iIndividualNum[iGroupDimNum - 1]):
            #1
            AssignValueToArray(dSumEtoU, 0, iNestLayerNum - 1, 0, iChoiceNum[pyidxNestLayerNum - 1] - 1, 0)
            iRealChoice = 0
            for iChoice in range(0, iChoiceNum[pyidxNestLayerNum] - 1):
                if bDummyFlag[pyidxNestLayerNum, iChoice] == 0:
                    dCost[pyidxNestLayerNum, iChoice] = dExteremeHighPrice
                    dEtoU[pyidxNestLayerNum, iChoice] = 0
                else:
                    if YearOnMarket[iRealChoice] <= iStepIndex:
                        dCost[pyidxNestLayerNum, iChoice] = generalizedcost[iRealChoice, iStepIndex]
                    else:
                        dCost[pyidxNestLayerNum, iChoice] = dExteremeHighPrice
                    #calculate dCost(iNestLayerNum, i)
                    #function of dLamda, and attributes; form depends on attributes and parameters setting
                    iTemp = math.trunc((iChoice - 1) / iNestPerNestNum[pyidxNestLayerNum]) + 1
                    dEtoU[pyidxNestLayerNum, iChoice] = math.exp(dBeta[pyidxNestLayerNum, iTemp] * dCost[pyidxNestLayerNum, iChoice])
                    #calculate dSumEtoU(iNestLayerNum, i)
                    dSumEtoU[pyidxNestLayerNum, iTemp] = dSumEtoU[pyidxNestLayerNum, iTemp] + dEtoU[pyidxNestLayerNum, iChoice]
                    iRealChoice = iRealChoice + 1
            #calculate dProb(iNestLayerNum, i)
            for iChoice in range(0, iChoiceNum[pyidxNestLayerNum] - 1):
                iTemp = math.trunc((iChoice - 1) / iNestPerNestNum[pyidxNestLayerNum]) + 1
                if bDummyFlag[pyidxNestLayerNum, iChoice] == 0:
                    dProb[pyidxNestLayerNum, iChoice] = 0
                elif bDummyFlag[pyidxNestLayerNum, iChoice] == 100:
                    dProb[pyidxNestLayerNum, iChoice] = 1
                elif dSumEtoU[pyidxNestLayerNum, iTemp] == 0:
                    dTemp = 0
                    for iTemp2 in range(0, iNestPerNestNum[pyidxNestLayerNum] - 1):
                        dTemp = dTemp + bDummyFlag[pyidxNestLayerNum, ( iTemp - 1 )  * iNestPerNestNum[pyidxNestLayerNum] + iTemp2]
                    dProb[pyidxNestLayerNum, iChoice] = 1 / dTemp / 11
                else:
                    dProb[pyidxNestLayerNum, iChoice] = dEtoU[pyidxNestLayerNum, iChoice] / dSumEtoU[pyidxNestLayerNum, iTemp]
            for iLayer in range((iNestLayerNum - 2), 0, - 1):
                #2
                for iNest in range(0, iChoiceNum[iLayer] - 1):
                    #3
                    if bDummyFlag[iLayer, iNest] == 0 or dSumEtoU[iLayer + 1, iNest] == 0:
                        dCost[iLayer, iNest] = dExteremeHighPrice
                        dEtoU[iLayer, iNest] = 0
                    else:
                        #calculate dCost(iLayer, iNest)
                        dCost[iLayer, iNest] = math.log(dSumEtoU[iLayer + 1, iNest]) / dBeta[iLayer + 1, iNest]
                        #calculate dEtoU(iLayer, iNest)
                        iTemp = math.trunc(( iNest - 1 )  / iNestPerNestNum[iLayer]) + 1
                        dEtoU[iLayer, iNest] = math.exp(dBeta[iLayer, iTemp] * dCost[iLayer, iNest])
                        #calculate dSumEtoU(iNestLayerNum, i)
                        dSumEtoU[iLayer, iTemp] = dSumEtoU[iLayer, iTemp] + dEtoU[iLayer, iNest]
                    #3
                #calculate dProb(iLayer, iNest)
                for iNest in range(0, iChoiceNum[iLayer] - 1):
                    iTemp = math.trunc((iNest - 1) / iNestPerNestNum[iLayer]) + 1
                    if bDummyFlag[iLayer, iNest] == 0:
                        dProb[iLayer, iNest] = 0
                    elif bDummyFlag[iLayer, iNest] == 100:
                        dProb[iLayer, iNest] = 1
                    elif dSumEtoU[iLayer, iTemp] == 0:
                        dTemp = 0
                        for iTemp2 in range(0, iNestPerNestNum[iLayer] - 1):
                            dTemp = dTemp + bDummyFlag[iLayer, (iTemp - 1) * iNestPerNestNum[iLayer] + iTemp2]
                        dProb[iLayer, iNest] = 1 / dTemp / 11
                    else:
                        dProb[iLayer, iNest] = dEtoU[iLayer, iNest] / dSumEtoU[iLayer, iTemp]
                #2
            #1
    np.savetxt(rootdir + 'dProb.csv', dProb, delimiter=',')

def AssignValueToArray(LcTargetArray, iLcRowL, iLcRowU, iLcColL, iLcColU, LcSourceArray):
    # check dimensionality of target array. If 2 dim, then iLcDim=2. If 1 dim, then iLcDim=1
    iLcDim = LcTargetArray.ndim
    # check dimensionality of source array. If 2 dim, then iLcDimS=2. If 1 dim, then iLcDimS=1
    iLcDimS = LcSourceArray.ndim

    if isinstance(LcSourceArray, np.ndarray):
        if iLcRowL == iLcRowU:
            if iLcDimS == 1:
                if iLcDim == 2:
                    for iLcCol in range(iLcColL, iLcColU):
                        LcTargetArray[iLcRowL, iLcCol] = LcSourceArray[iLcCol + 1 - iLcColL]
                else:
                    for iLcCol in range(iLcColL, iLcColU):
                        LcTargetArray[iLcCol] = LcSourceArray[iLcCol + 1 - iLcColL]
            else:
                if iLcDim == 2:
                    for iLcCol in range(iLcColL, iLcColU):
                        LcTargetArray[iLcRowL, iLcCol] = LcSourceArray[1, iLcCol + 1 - iLcColL]
                else:
                    for iLcCol in range(iLcColL, iLcColU):
                        LcTargetArray[iLcCol] = LcSourceArray[1, iLcCol + 1 - iLcColL]
        elif iLcColL == iLcColU:
            if iLcDim == 2:
                for iLcRow in range(iLcRowL, iLcRowU):
                    LcTargetArray[iLcRow, iLcColL] = LcSourceArray[iLcRow + 1 - iLcRowL]
            else:
                for iLcRow in range(iLcRowL, iLcRowU):
                    LcTargetArray[iLcRow] = LcSourceArray[iLcRow + 1 - iLcRowL]
        else:
            for iLcRow in range(iLcRowL, iLcRowU):
                for iLcCol in range(iLcColL, iLcColU):
                    LcTargetArray[iLcRow, iLcCol] = LcSourceArray[iLcRow + 1 - iLcRowL, iLcCol + 1 - iLcColL]
    else:
        if iLcRowL == iLcRowU and iLcDim == 1:
            for iLcCol in range(iLcColL, iLcColU):
                LcTargetArray[iLcCol] = LcSourceArray
        elif iLcColL == iLcColU and iLcDim == 1:
            for iLcRow in range(iLcRowL, iLcRowU):
                LcTargetArray[iLcRow] = LcSourceArray
        else:
            for iLcRow in range(iLcRowL, iLcRowU):
                for iLcCol in range(iLcColL, iLcColU):
                    LcTargetArray[iLcRow, iLcCol] = LcSourceArray

# main
PHEVT_Consumer()
