// FUNCTION
REAL ___CLX_CLAMPREAL(
  BOOL EN, 
  BOOL *__ENO, 
  REAL VALUE, 
  REAL MINVALUE, 
  REAL MAXVALUE)
{
  BOOL ENO = __BOOL_LITERAL(TRUE);
  REAL CLX_CLAMPREAL = 0;

  // Control execution
  if (!EN) {
    if (__ENO != NULL) {
      *__ENO = __BOOL_LITERAL(FALSE);
    }
    return CLX_CLAMPREAL;
  }
  if ((VALUE < MINVALUE)) {
    CLX_CLAMPREAL = MINVALUE;
  } else if ((VALUE > MAXVALUE)) {
    CLX_CLAMPREAL = MAXVALUE;
  } else {
    CLX_CLAMPREAL = VALUE;
  };

  goto __end;

__end:
  if (__ENO != NULL) {
    *__ENO = ENO;
  }
  return CLX_CLAMPREAL;
}


void CLX_0003_init__(CLX_0003_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,AIT_2301,data__->AIT_2301,retain)
  __INIT_EXTERNAL(REAL,AIT_2301_HH_SP,data__->AIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(REAL,AIT_2301_HI_SP,data__->AIT_2301_HI_SP,retain)
  __INIT_EXTERNAL(REAL,AIT_2301_LL_SP,data__->AIT_2301_LL_SP,retain)
  __INIT_EXTERNAL(REAL,AIT_2301_LO_SP,data__->AIT_2301_LO_SP,retain)
  __INIT_EXTERNAL(BOOL,ALM_AIT_2301_HH,data__->ALM_AIT_2301_HH,retain)
  __INIT_EXTERNAL(BOOL,ALM_AIT_2301_HI,data__->ALM_AIT_2301_HI,retain)
  __INIT_EXTERNAL(BOOL,ALM_AIT_2301_LL,data__->ALM_AIT_2301_LL,retain)
  __INIT_EXTERNAL(BOOL,ALM_AIT_2301_LO,data__->ALM_AIT_2301_LO,retain)
  __INIT_EXTERNAL(BOOL,ALM_BL_4001_FAULT,data__->ALM_BL_4001_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_BL_4002_FAULT,data__->ALM_BL_4002_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_DPIT_2101_HH,data__->ALM_DPIT_2101_HH,retain)
  __INIT_EXTERNAL(BOOL,ALM_DPIT_2101_HI,data__->ALM_DPIT_2101_HI,retain)
  __INIT_EXTERNAL(BOOL,ALM_DPIT_2101_LL,data__->ALM_DPIT_2101_LL,retain)
  __INIT_EXTERNAL(BOOL,ALM_DPIT_2101_LO,data__->ALM_DPIT_2101_LO,retain)
  __INIT_EXTERNAL(BOOL,ALM_FCV_2301_FAULT,data__->ALM_FCV_2301_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_FIT_2301_HH,data__->ALM_FIT_2301_HH,retain)
  __INIT_EXTERNAL(BOOL,ALM_FIT_2301_HI,data__->ALM_FIT_2301_HI,retain)
  __INIT_EXTERNAL(BOOL,ALM_FIT_2301_LL,data__->ALM_FIT_2301_LL,retain)
  __INIT_EXTERNAL(BOOL,ALM_FIT_2301_LO,data__->ALM_FIT_2301_LO,retain)
  __INIT_EXTERNAL(BOOL,ALM_FIT_4501_HH,data__->ALM_FIT_4501_HH,retain)
  __INIT_EXTERNAL(BOOL,ALM_FIT_4501_HI,data__->ALM_FIT_4501_HI,retain)
  __INIT_EXTERNAL(BOOL,ALM_FIT_4501_LL,data__->ALM_FIT_4501_LL,retain)
  __INIT_EXTERNAL(BOOL,ALM_FIT_4501_LO,data__->ALM_FIT_4501_LO,retain)
  __INIT_EXTERNAL(BOOL,ALM_LIT_2001_HH,data__->ALM_LIT_2001_HH,retain)
  __INIT_EXTERNAL(BOOL,ALM_LIT_2001_HI,data__->ALM_LIT_2001_HI,retain)
  __INIT_EXTERNAL(BOOL,ALM_LIT_2001_LL,data__->ALM_LIT_2001_LL,retain)
  __INIT_EXTERNAL(BOOL,ALM_LIT_2001_LO,data__->ALM_LIT_2001_LO,retain)
  __INIT_EXTERNAL(BOOL,ALM_LIT_2601_HH,data__->ALM_LIT_2601_HH,retain)
  __INIT_EXTERNAL(BOOL,ALM_LIT_2601_HI,data__->ALM_LIT_2601_HI,retain)
  __INIT_EXTERNAL(BOOL,ALM_LIT_2601_LL,data__->ALM_LIT_2601_LL,retain)
  __INIT_EXTERNAL(BOOL,ALM_LIT_2601_LO,data__->ALM_LIT_2601_LO,retain)
  __INIT_EXTERNAL(BOOL,ALM_PIT_4001_HH,data__->ALM_PIT_4001_HH,retain)
  __INIT_EXTERNAL(BOOL,ALM_PIT_4001_HI,data__->ALM_PIT_4001_HI,retain)
  __INIT_EXTERNAL(BOOL,ALM_PIT_4001_LL,data__->ALM_PIT_4001_LL,retain)
  __INIT_EXTERNAL(BOOL,ALM_PIT_4001_LO,data__->ALM_PIT_4001_LO,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2001_FAULT,data__->ALM_PMP_2001_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2002_FAULT,data__->ALM_PMP_2002_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2201_FAULT,data__->ALM_PMP_2201_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2601_FAULT,data__->ALM_PMP_2601_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2602_FAULT,data__->ALM_PMP_2602_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_4501_FAULT,data__->ALM_PMP_4501_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_4502_FAULT,data__->ALM_PMP_4502_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_P_20_FAULT,data__->ALM_P_20_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_VAL_2201_FAULT,data__->ALM_VAL_2201_FAULT,retain)
  __INIT_EXTERNAL(BOOL,BL_4001_FAULT,data__->BL_4001_FAULT,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_FAULT,data__->BL_4002_FAULT,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101,data__->DPIT_2101,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101_HH_SP,data__->DPIT_2101_HH_SP,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101_HI_SP,data__->DPIT_2101_HI_SP,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101_LL_SP,data__->DPIT_2101_LL_SP,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101_LO_SP,data__->DPIT_2101_LO_SP,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_FAULT,data__->FCV_2301_FAULT,retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HI_SP,data__->FIT_2301_HI_SP,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_LL_SP,data__->FIT_2301_LL_SP,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_LO_SP,data__->FIT_2301_LO_SP,retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HI_SP,data__->FIT_4501_HI_SP,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_LL_SP,data__->FIT_4501_LL_SP,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_LO_SP,data__->FIT_4501_LO_SP,retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HI_SP,data__->LIT_2001_HI_SP,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_LL_SP,data__->LIT_2001_LL_SP,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_LO_SP,data__->LIT_2001_LO_SP,retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HI_SP,data__->LIT_2601_HI_SP,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_LL_SP,data__->LIT_2601_LL_SP,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_LO_SP,data__->LIT_2601_LO_SP,retain)
  __INIT_EXTERNAL(REAL,PIT_4001,data__->PIT_4001,retain)
  __INIT_EXTERNAL(REAL,PIT_4001_HH_SP,data__->PIT_4001_HH_SP,retain)
  __INIT_EXTERNAL(REAL,PIT_4001_HI_SP,data__->PIT_4001_HI_SP,retain)
  __INIT_EXTERNAL(REAL,PIT_4001_LL_SP,data__->PIT_4001_LL_SP,retain)
  __INIT_EXTERNAL(REAL,PIT_4001_LO_SP,data__->PIT_4001_LO_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_FAULT,data__->PMP_2001_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_FAULT,data__->PMP_2002_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_FAULT,data__->PMP_2201_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_FAULT,data__->PMP_2601_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_FAULT,data__->PMP_2602_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_FAULT,data__->PMP_4501_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_FAULT,data__->PMP_4502_FAULT,retain)
  __INIT_EXTERNAL(BOOL,P_20_FAULT,data__->P_20_FAULT,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_FAULT,data__->VAL_2201_FAULT,retain)
  __INIT_VAR(data__->CLX_0237,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0238,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0239,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0240,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0241,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0242,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0243,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0244,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0245,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0246,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0247,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0248,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0249,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0250,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0251,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0252,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0253,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0254,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0255,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0256,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0257,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0258,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0259,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0260,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0261,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0262,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0263,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0264,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0265,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0266,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0267,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0268,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0269,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0270,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0271,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0272,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0273,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0274,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0275,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0276,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0003_body__(CLX_0003_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,CLX_0237,,(__GET_EXTERNAL(data__->AIT_2301,) >= __GET_EXTERNAL(data__->AIT_2301_HI_SP,)));
  if (__GET_VAR(data__->CLX_0237,)) {
    __SET_EXTERNAL(data__->,ALM_AIT_2301_HI,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_AIT_2301_HI,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0238,,(__GET_EXTERNAL(data__->AIT_2301,) >= __GET_EXTERNAL(data__->AIT_2301_HH_SP,)));
  if (__GET_VAR(data__->CLX_0238,)) {
    __SET_EXTERNAL(data__->,ALM_AIT_2301_HH,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_AIT_2301_HH,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0239,,(__GET_EXTERNAL(data__->AIT_2301,) <= __GET_EXTERNAL(data__->AIT_2301_LO_SP,)));
  if (__GET_VAR(data__->CLX_0239,)) {
    __SET_EXTERNAL(data__->,ALM_AIT_2301_LO,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_AIT_2301_LO,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0240,,(__GET_EXTERNAL(data__->AIT_2301,) <= __GET_EXTERNAL(data__->AIT_2301_LL_SP,)));
  if (__GET_VAR(data__->CLX_0240,)) {
    __SET_EXTERNAL(data__->,ALM_AIT_2301_LL,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_AIT_2301_LL,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0241,,(__GET_EXTERNAL(data__->DPIT_2101,) >= __GET_EXTERNAL(data__->DPIT_2101_HI_SP,)));
  if (__GET_VAR(data__->CLX_0241,)) {
    __SET_EXTERNAL(data__->,ALM_DPIT_2101_HI,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_DPIT_2101_HI,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0242,,(__GET_EXTERNAL(data__->DPIT_2101,) >= __GET_EXTERNAL(data__->DPIT_2101_HH_SP,)));
  if (__GET_VAR(data__->CLX_0242,)) {
    __SET_EXTERNAL(data__->,ALM_DPIT_2101_HH,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_DPIT_2101_HH,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0243,,(__GET_EXTERNAL(data__->DPIT_2101,) <= __GET_EXTERNAL(data__->DPIT_2101_LO_SP,)));
  if (__GET_VAR(data__->CLX_0243,)) {
    __SET_EXTERNAL(data__->,ALM_DPIT_2101_LO,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_DPIT_2101_LO,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0244,,(__GET_EXTERNAL(data__->DPIT_2101,) <= __GET_EXTERNAL(data__->DPIT_2101_LL_SP,)));
  if (__GET_VAR(data__->CLX_0244,)) {
    __SET_EXTERNAL(data__->,ALM_DPIT_2101_LL,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_DPIT_2101_LL,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0245,,(__GET_EXTERNAL(data__->PIT_4001,) >= __GET_EXTERNAL(data__->PIT_4001_HI_SP,)));
  if (__GET_VAR(data__->CLX_0245,)) {
    __SET_EXTERNAL(data__->,ALM_PIT_4001_HI,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PIT_4001_HI,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0246,,(__GET_EXTERNAL(data__->PIT_4001,) >= __GET_EXTERNAL(data__->PIT_4001_HH_SP,)));
  if (__GET_VAR(data__->CLX_0246,)) {
    __SET_EXTERNAL(data__->,ALM_PIT_4001_HH,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PIT_4001_HH,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0247,,(__GET_EXTERNAL(data__->PIT_4001,) <= __GET_EXTERNAL(data__->PIT_4001_LO_SP,)));
  if (__GET_VAR(data__->CLX_0247,)) {
    __SET_EXTERNAL(data__->,ALM_PIT_4001_LO,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PIT_4001_LO,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0248,,(__GET_EXTERNAL(data__->PIT_4001,) <= __GET_EXTERNAL(data__->PIT_4001_LL_SP,)));
  if (__GET_VAR(data__->CLX_0248,)) {
    __SET_EXTERNAL(data__->,ALM_PIT_4001_LL,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PIT_4001_LL,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0249,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HI_SP,)));
  if (__GET_VAR(data__->CLX_0249,)) {
    __SET_EXTERNAL(data__->,ALM_FIT_2301_HI,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FIT_2301_HI,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0250,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->CLX_0250,)) {
    __SET_EXTERNAL(data__->,ALM_FIT_2301_HH,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FIT_2301_HH,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0251,,(__GET_EXTERNAL(data__->FIT_2301,) <= __GET_EXTERNAL(data__->FIT_2301_LO_SP,)));
  if (__GET_VAR(data__->CLX_0251,)) {
    __SET_EXTERNAL(data__->,ALM_FIT_2301_LO,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FIT_2301_LO,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0252,,(__GET_EXTERNAL(data__->FIT_2301,) <= __GET_EXTERNAL(data__->FIT_2301_LL_SP,)));
  if (__GET_VAR(data__->CLX_0252,)) {
    __SET_EXTERNAL(data__->,ALM_FIT_2301_LL,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FIT_2301_LL,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0253,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HI_SP,)));
  if (__GET_VAR(data__->CLX_0253,)) {
    __SET_EXTERNAL(data__->,ALM_FIT_4501_HI,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FIT_4501_HI,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0254,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->CLX_0254,)) {
    __SET_EXTERNAL(data__->,ALM_FIT_4501_HH,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FIT_4501_HH,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0255,,(__GET_EXTERNAL(data__->FIT_4501,) <= __GET_EXTERNAL(data__->FIT_4501_LO_SP,)));
  if (__GET_VAR(data__->CLX_0255,)) {
    __SET_EXTERNAL(data__->,ALM_FIT_4501_LO,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FIT_4501_LO,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0256,,(__GET_EXTERNAL(data__->FIT_4501,) <= __GET_EXTERNAL(data__->FIT_4501_LL_SP,)));
  if (__GET_VAR(data__->CLX_0256,)) {
    __SET_EXTERNAL(data__->,ALM_FIT_4501_LL,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FIT_4501_LL,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0257,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HI_SP,)));
  if (__GET_VAR(data__->CLX_0257,)) {
    __SET_EXTERNAL(data__->,ALM_LIT_2001_HI,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_LIT_2001_HI,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0258,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->CLX_0258,)) {
    __SET_EXTERNAL(data__->,ALM_LIT_2001_HH,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_LIT_2001_HH,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0259,,(__GET_EXTERNAL(data__->LIT_2001,) <= __GET_EXTERNAL(data__->LIT_2001_LO_SP,)));
  if (__GET_VAR(data__->CLX_0259,)) {
    __SET_EXTERNAL(data__->,ALM_LIT_2001_LO,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_LIT_2001_LO,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0260,,(__GET_EXTERNAL(data__->LIT_2001,) <= __GET_EXTERNAL(data__->LIT_2001_LL_SP,)));
  if (__GET_VAR(data__->CLX_0260,)) {
    __SET_EXTERNAL(data__->,ALM_LIT_2001_LL,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_LIT_2001_LL,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0261,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HI_SP,)));
  if (__GET_VAR(data__->CLX_0261,)) {
    __SET_EXTERNAL(data__->,ALM_LIT_2601_HI,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_LIT_2601_HI,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0262,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->CLX_0262,)) {
    __SET_EXTERNAL(data__->,ALM_LIT_2601_HH,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_LIT_2601_HH,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0263,,(__GET_EXTERNAL(data__->LIT_2601,) <= __GET_EXTERNAL(data__->LIT_2601_LO_SP,)));
  if (__GET_VAR(data__->CLX_0263,)) {
    __SET_EXTERNAL(data__->,ALM_LIT_2601_LO,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_LIT_2601_LO,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0264,,(__GET_EXTERNAL(data__->LIT_2601,) <= __GET_EXTERNAL(data__->LIT_2601_LL_SP,)));
  if (__GET_VAR(data__->CLX_0264,)) {
    __SET_EXTERNAL(data__->,ALM_LIT_2601_LL,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_LIT_2601_LL,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0265,,(__GET_EXTERNAL(data__->BL_4001_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0265,)) {
    __SET_EXTERNAL(data__->,ALM_BL_4001_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_BL_4001_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0266,,(__GET_EXTERNAL(data__->BL_4002_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0266,)) {
    __SET_EXTERNAL(data__->,ALM_BL_4002_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_BL_4002_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0267,,(__GET_EXTERNAL(data__->FCV_2301_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0267,)) {
    __SET_EXTERNAL(data__->,ALM_FCV_2301_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_FCV_2301_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0268,,(__GET_EXTERNAL(data__->P_20_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0268,)) {
    __SET_EXTERNAL(data__->,ALM_P_20_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_P_20_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0269,,(__GET_EXTERNAL(data__->PMP_2001_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0269,)) {
    __SET_EXTERNAL(data__->,ALM_PMP_2001_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PMP_2001_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0270,,(__GET_EXTERNAL(data__->PMP_2002_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0270,)) {
    __SET_EXTERNAL(data__->,ALM_PMP_2002_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PMP_2002_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0271,,(__GET_EXTERNAL(data__->PMP_2201_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0271,)) {
    __SET_EXTERNAL(data__->,ALM_PMP_2201_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PMP_2201_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0272,,(__GET_EXTERNAL(data__->PMP_2601_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0272,)) {
    __SET_EXTERNAL(data__->,ALM_PMP_2601_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PMP_2601_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0273,,(__GET_EXTERNAL(data__->PMP_2602_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0273,)) {
    __SET_EXTERNAL(data__->,ALM_PMP_2602_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PMP_2602_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0274,,(__GET_EXTERNAL(data__->PMP_4501_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0274,)) {
    __SET_EXTERNAL(data__->,ALM_PMP_4501_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PMP_4501_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0275,,(__GET_EXTERNAL(data__->PMP_4502_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0275,)) {
    __SET_EXTERNAL(data__->,ALM_PMP_4502_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_PMP_4502_FAULT,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0276,,(__GET_EXTERNAL(data__->VAL_2201_FAULT,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->CLX_0276,)) {
    __SET_EXTERNAL(data__->,ALM_VAL_2201_FAULT,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_EXTERNAL(data__->,ALM_VAL_2201_FAULT,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0003_body__() 





void CLX_0113_init__(CLX_0113_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,AIT_2301,data__->AIT_2301,retain)
  __INIT_EXTERNAL(REAL,AIT_2301_SP,data__->AIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_AUTO,data__->FCV_2301_AUTO,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_ENABLE,data__->FCV_2301_ENABLE,retain)
  __INIT_EXTERNAL(REAL,FCV_2301_OUT,data__->FCV_2301_OUT,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0283,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0284,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0285,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0286,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0287,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0288,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0113_body__(CLX_0113_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->FCV_2301_ENABLE,) && __GET_EXTERNAL(data__->FCV_2301_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->AIT_2301_SP,) - __GET_EXTERNAL(data__->AIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0283,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0284,)) * __GET_VAR(data__->CLX_0286,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0285,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0286,)));
    __SET_VAR(data__->,CLX_0287,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0288,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0287,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_EXTERNAL(data__->,FCV_2301_OUT,,__GET_VAR(data__->CLX_0288,));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0113_body__() 





void CLX_0115_init__(CLX_0115_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,AIT_2301,data__->AIT_2301,retain)
  __INIT_EXTERNAL(REAL,AIT_2301_SP,data__->AIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_AUTO,data__->VAL_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_ENABLE,data__->VAL_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0289,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0290,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0291,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0292,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0293,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0294,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0115_body__(CLX_0115_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->VAL_2201_ENABLE,) && __GET_EXTERNAL(data__->VAL_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->AIT_2301_SP,) - __GET_EXTERNAL(data__->AIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0289,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0290,)) * __GET_VAR(data__->CLX_0292,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0291,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0292,)));
    __SET_VAR(data__->,CLX_0293,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0294,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0293,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0115_body__() 





void CLX_0117_init__(CLX_0117_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,DPIT_2101,data__->DPIT_2101,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101_SP,data__->DPIT_2101_SP,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_AUTO,data__->FCV_2301_AUTO,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_ENABLE,data__->FCV_2301_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0295,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0296,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0297,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0298,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0299,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0300,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0117_body__(CLX_0117_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->FCV_2301_ENABLE,) && __GET_EXTERNAL(data__->FCV_2301_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->DPIT_2101_SP,) - __GET_EXTERNAL(data__->DPIT_2101,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0295,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0296,)) * __GET_VAR(data__->CLX_0298,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0297,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0298,)));
    __SET_VAR(data__->,CLX_0299,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0300,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0299,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0117_body__() 





void CLX_0119_init__(CLX_0119_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,DPIT_2101,data__->DPIT_2101,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101_SP,data__->DPIT_2101_SP,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_AUTO,data__->VAL_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_ENABLE,data__->VAL_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0301,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0302,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0303,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0304,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0305,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0306,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0119_body__(CLX_0119_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->VAL_2201_ENABLE,) && __GET_EXTERNAL(data__->VAL_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->DPIT_2101_SP,) - __GET_EXTERNAL(data__->DPIT_2101,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0301,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0302,)) * __GET_VAR(data__->CLX_0304,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0303,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0304,)));
    __SET_VAR(data__->,CLX_0305,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0306,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0305,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0119_body__() 





void CLX_0135_init__(CLX_0135_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_SP,data__->FIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_AUTO,data__->P_20_AUTO,retain)
  __INIT_EXTERNAL(BOOL,P_20_ENABLE,data__->P_20_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0307,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0308,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0309,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0310,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0311,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0312,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0135_body__(CLX_0135_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->P_20_ENABLE,) && __GET_EXTERNAL(data__->P_20_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_2301_SP,) - __GET_EXTERNAL(data__->FIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0307,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0308,)) * __GET_VAR(data__->CLX_0310,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0309,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0310,)));
    __SET_VAR(data__->,CLX_0311,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0312,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0311,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0135_body__() 





void CLX_0121_init__(CLX_0121_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_SP,data__->FIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_AUTO,data__->PMP_2001_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_ENABLE,data__->PMP_2001_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0313,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0314,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0315,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0316,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0317,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0318,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0121_body__(CLX_0121_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2001_ENABLE,) && __GET_EXTERNAL(data__->PMP_2001_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_2301_SP,) - __GET_EXTERNAL(data__->FIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0313,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0314,)) * __GET_VAR(data__->CLX_0316,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0315,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0316,)));
    __SET_VAR(data__->,CLX_0317,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0318,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0317,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0121_body__() 





void CLX_0123_init__(CLX_0123_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_SP,data__->FIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_AUTO,data__->PMP_2002_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_ENABLE,data__->PMP_2002_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0319,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0320,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0321,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0322,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0323,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0324,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0123_body__(CLX_0123_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2002_ENABLE,) && __GET_EXTERNAL(data__->PMP_2002_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_2301_SP,) - __GET_EXTERNAL(data__->FIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0319,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0320,)) * __GET_VAR(data__->CLX_0322,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0321,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0322,)));
    __SET_VAR(data__->,CLX_0323,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0324,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0323,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0123_body__() 





void CLX_0125_init__(CLX_0125_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_SP,data__->FIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_AUTO,data__->PMP_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_ENABLE,data__->PMP_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0325,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0326,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0327,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0328,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0329,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0330,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0125_body__(CLX_0125_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2201_ENABLE,) && __GET_EXTERNAL(data__->PMP_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_2301_SP,) - __GET_EXTERNAL(data__->FIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0325,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0326,)) * __GET_VAR(data__->CLX_0328,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0327,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0328,)));
    __SET_VAR(data__->,CLX_0329,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0330,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0329,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0125_body__() 





void CLX_0127_init__(CLX_0127_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_SP,data__->FIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_AUTO,data__->PMP_2601_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_ENABLE,data__->PMP_2601_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0331,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0332,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0333,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0334,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0335,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0336,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0127_body__(CLX_0127_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2601_ENABLE,) && __GET_EXTERNAL(data__->PMP_2601_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_2301_SP,) - __GET_EXTERNAL(data__->FIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0331,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0332,)) * __GET_VAR(data__->CLX_0334,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0333,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0334,)));
    __SET_VAR(data__->,CLX_0335,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0336,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0335,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0127_body__() 





void CLX_0129_init__(CLX_0129_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_SP,data__->FIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_AUTO,data__->PMP_2602_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_ENABLE,data__->PMP_2602_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0337,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0338,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0339,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0340,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0341,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0342,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0129_body__(CLX_0129_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2602_ENABLE,) && __GET_EXTERNAL(data__->PMP_2602_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_2301_SP,) - __GET_EXTERNAL(data__->FIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0337,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0338,)) * __GET_VAR(data__->CLX_0340,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0339,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0340,)));
    __SET_VAR(data__->,CLX_0341,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0342,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0341,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0129_body__() 





void CLX_0131_init__(CLX_0131_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_SP,data__->FIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_AUTO,data__->PMP_4501_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_ENABLE,data__->PMP_4501_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0343,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0344,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0345,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0346,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0347,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0348,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0131_body__(CLX_0131_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4501_ENABLE,) && __GET_EXTERNAL(data__->PMP_4501_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_2301_SP,) - __GET_EXTERNAL(data__->FIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0343,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0344,)) * __GET_VAR(data__->CLX_0346,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0345,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0346,)));
    __SET_VAR(data__->,CLX_0347,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0348,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0347,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0131_body__() 





void CLX_0133_init__(CLX_0133_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_SP,data__->FIT_2301_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_AUTO,data__->PMP_4502_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_ENABLE,data__->PMP_4502_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0349,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0350,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0351,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0352,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0353,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0354,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0133_body__(CLX_0133_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4502_ENABLE,) && __GET_EXTERNAL(data__->PMP_4502_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_2301_SP,) - __GET_EXTERNAL(data__->FIT_2301,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0349,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0350,)) * __GET_VAR(data__->CLX_0352,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0351,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0352,)));
    __SET_VAR(data__->,CLX_0353,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0354,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0353,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0133_body__() 





void CLX_0151_init__(CLX_0151_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_SP,data__->FIT_4501_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_AUTO,data__->P_20_AUTO,retain)
  __INIT_EXTERNAL(BOOL,P_20_ENABLE,data__->P_20_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0355,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0356,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0357,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0358,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0359,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0360,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0151_body__(CLX_0151_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->P_20_ENABLE,) && __GET_EXTERNAL(data__->P_20_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_4501_SP,) - __GET_EXTERNAL(data__->FIT_4501,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0355,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0356,)) * __GET_VAR(data__->CLX_0358,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0357,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0358,)));
    __SET_VAR(data__->,CLX_0359,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0360,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0359,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0151_body__() 





void CLX_0137_init__(CLX_0137_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_SP,data__->FIT_4501_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_AUTO,data__->PMP_2001_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_ENABLE,data__->PMP_2001_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0361,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0362,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0363,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0364,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0365,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0366,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0137_body__(CLX_0137_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2001_ENABLE,) && __GET_EXTERNAL(data__->PMP_2001_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_4501_SP,) - __GET_EXTERNAL(data__->FIT_4501,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0361,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0362,)) * __GET_VAR(data__->CLX_0364,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0363,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0364,)));
    __SET_VAR(data__->,CLX_0365,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0366,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0365,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0137_body__() 





void CLX_0139_init__(CLX_0139_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_SP,data__->FIT_4501_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_AUTO,data__->PMP_2002_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_ENABLE,data__->PMP_2002_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0367,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0368,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0369,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0370,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0371,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0372,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0139_body__(CLX_0139_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2002_ENABLE,) && __GET_EXTERNAL(data__->PMP_2002_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_4501_SP,) - __GET_EXTERNAL(data__->FIT_4501,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0367,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0368,)) * __GET_VAR(data__->CLX_0370,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0369,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0370,)));
    __SET_VAR(data__->,CLX_0371,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0372,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0371,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0139_body__() 





void CLX_0141_init__(CLX_0141_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_SP,data__->FIT_4501_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_AUTO,data__->PMP_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_ENABLE,data__->PMP_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0373,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0374,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0375,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0376,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0377,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0378,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0141_body__(CLX_0141_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2201_ENABLE,) && __GET_EXTERNAL(data__->PMP_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_4501_SP,) - __GET_EXTERNAL(data__->FIT_4501,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0373,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0374,)) * __GET_VAR(data__->CLX_0376,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0375,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0376,)));
    __SET_VAR(data__->,CLX_0377,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0378,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0377,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0141_body__() 





void CLX_0143_init__(CLX_0143_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_SP,data__->FIT_4501_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_AUTO,data__->PMP_2601_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_ENABLE,data__->PMP_2601_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0379,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0380,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0381,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0382,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0383,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0384,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0143_body__(CLX_0143_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2601_ENABLE,) && __GET_EXTERNAL(data__->PMP_2601_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_4501_SP,) - __GET_EXTERNAL(data__->FIT_4501,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0379,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0380,)) * __GET_VAR(data__->CLX_0382,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0381,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0382,)));
    __SET_VAR(data__->,CLX_0383,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0384,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0383,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0143_body__() 





void CLX_0145_init__(CLX_0145_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_SP,data__->FIT_4501_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_AUTO,data__->PMP_2602_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_ENABLE,data__->PMP_2602_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0385,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0386,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0387,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0388,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0389,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0390,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0145_body__(CLX_0145_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2602_ENABLE,) && __GET_EXTERNAL(data__->PMP_2602_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_4501_SP,) - __GET_EXTERNAL(data__->FIT_4501,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0385,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0386,)) * __GET_VAR(data__->CLX_0388,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0387,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0388,)));
    __SET_VAR(data__->,CLX_0389,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0390,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0389,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0145_body__() 





void CLX_0147_init__(CLX_0147_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_SP,data__->FIT_4501_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_AUTO,data__->PMP_4501_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_ENABLE,data__->PMP_4501_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0391,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0392,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0393,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0394,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0395,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0396,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0147_body__(CLX_0147_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4501_ENABLE,) && __GET_EXTERNAL(data__->PMP_4501_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_4501_SP,) - __GET_EXTERNAL(data__->FIT_4501,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0391,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0392,)) * __GET_VAR(data__->CLX_0394,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0393,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0394,)));
    __SET_VAR(data__->,CLX_0395,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0396,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0395,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0147_body__() 





void CLX_0149_init__(CLX_0149_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_SP,data__->FIT_4501_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_AUTO,data__->PMP_4502_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_ENABLE,data__->PMP_4502_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0397,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0398,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0399,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0400,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0401,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0402,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0149_body__(CLX_0149_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4502_ENABLE,) && __GET_EXTERNAL(data__->PMP_4502_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->FIT_4501_SP,) - __GET_EXTERNAL(data__->FIT_4501,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0397,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0398,)) * __GET_VAR(data__->CLX_0400,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0399,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0400,)));
    __SET_VAR(data__->,CLX_0401,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0402,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0401,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0149_body__() 





void CLX_0167_init__(CLX_0167_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_SP,data__->LIT_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_AUTO,data__->P_20_AUTO,retain)
  __INIT_EXTERNAL(BOOL,P_20_ENABLE,data__->P_20_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0403,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0404,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0405,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0406,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0407,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0408,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0167_body__(CLX_0167_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->P_20_ENABLE,) && __GET_EXTERNAL(data__->P_20_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2001_SP,) - __GET_EXTERNAL(data__->LIT_2001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0403,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0404,)) * __GET_VAR(data__->CLX_0406,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0405,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0406,)));
    __SET_VAR(data__->,CLX_0407,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0408,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0407,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0167_body__() 





void CLX_0153_init__(CLX_0153_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_SP,data__->LIT_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_AUTO,data__->PMP_2001_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_ENABLE,data__->PMP_2001_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0409,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0410,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0411,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0412,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0413,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0414,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0153_body__(CLX_0153_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2001_ENABLE,) && __GET_EXTERNAL(data__->PMP_2001_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2001_SP,) - __GET_EXTERNAL(data__->LIT_2001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0409,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0410,)) * __GET_VAR(data__->CLX_0412,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0411,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0412,)));
    __SET_VAR(data__->,CLX_0413,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0414,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0413,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0153_body__() 





void CLX_0155_init__(CLX_0155_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_SP,data__->LIT_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_AUTO,data__->PMP_2002_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_ENABLE,data__->PMP_2002_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0415,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0416,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0417,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0418,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0419,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0420,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0155_body__(CLX_0155_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2002_ENABLE,) && __GET_EXTERNAL(data__->PMP_2002_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2001_SP,) - __GET_EXTERNAL(data__->LIT_2001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0415,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0416,)) * __GET_VAR(data__->CLX_0418,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0417,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0418,)));
    __SET_VAR(data__->,CLX_0419,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0420,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0419,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0155_body__() 





void CLX_0157_init__(CLX_0157_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_SP,data__->LIT_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_AUTO,data__->PMP_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_ENABLE,data__->PMP_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0421,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0422,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0423,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0424,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0425,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0426,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0157_body__(CLX_0157_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2201_ENABLE,) && __GET_EXTERNAL(data__->PMP_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2001_SP,) - __GET_EXTERNAL(data__->LIT_2001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0421,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0422,)) * __GET_VAR(data__->CLX_0424,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0423,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0424,)));
    __SET_VAR(data__->,CLX_0425,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0426,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0425,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0157_body__() 





void CLX_0159_init__(CLX_0159_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_SP,data__->LIT_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_AUTO,data__->PMP_2601_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_ENABLE,data__->PMP_2601_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0427,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0428,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0429,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0430,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0431,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0432,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0159_body__(CLX_0159_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2601_ENABLE,) && __GET_EXTERNAL(data__->PMP_2601_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2001_SP,) - __GET_EXTERNAL(data__->LIT_2001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0427,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0428,)) * __GET_VAR(data__->CLX_0430,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0429,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0430,)));
    __SET_VAR(data__->,CLX_0431,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0432,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0431,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0159_body__() 





void CLX_0161_init__(CLX_0161_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_SP,data__->LIT_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_AUTO,data__->PMP_2602_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_ENABLE,data__->PMP_2602_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0433,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0434,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0435,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0436,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0437,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0438,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0161_body__(CLX_0161_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2602_ENABLE,) && __GET_EXTERNAL(data__->PMP_2602_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2001_SP,) - __GET_EXTERNAL(data__->LIT_2001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0433,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0434,)) * __GET_VAR(data__->CLX_0436,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0435,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0436,)));
    __SET_VAR(data__->,CLX_0437,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0438,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0437,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0161_body__() 





void CLX_0163_init__(CLX_0163_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_SP,data__->LIT_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_AUTO,data__->PMP_4501_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_ENABLE,data__->PMP_4501_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0439,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0440,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0441,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0442,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0443,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0444,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0163_body__(CLX_0163_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4501_ENABLE,) && __GET_EXTERNAL(data__->PMP_4501_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2001_SP,) - __GET_EXTERNAL(data__->LIT_2001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0439,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0440,)) * __GET_VAR(data__->CLX_0442,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0441,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0442,)));
    __SET_VAR(data__->,CLX_0443,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0444,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0443,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0163_body__() 





void CLX_0165_init__(CLX_0165_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_SP,data__->LIT_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_AUTO,data__->PMP_4502_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_ENABLE,data__->PMP_4502_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0445,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0446,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0447,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0448,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0449,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0450,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0165_body__(CLX_0165_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4502_ENABLE,) && __GET_EXTERNAL(data__->PMP_4502_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2001_SP,) - __GET_EXTERNAL(data__->LIT_2001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0445,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0446,)) * __GET_VAR(data__->CLX_0448,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0447,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0448,)));
    __SET_VAR(data__->,CLX_0449,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0450,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0449,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0165_body__() 





void CLX_0183_init__(CLX_0183_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_SP,data__->LIT_2601_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_AUTO,data__->P_20_AUTO,retain)
  __INIT_EXTERNAL(BOOL,P_20_ENABLE,data__->P_20_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0451,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0452,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0453,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0454,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0455,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0456,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0183_body__(CLX_0183_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->P_20_ENABLE,) && __GET_EXTERNAL(data__->P_20_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2601_SP,) - __GET_EXTERNAL(data__->LIT_2601,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0451,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0452,)) * __GET_VAR(data__->CLX_0454,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0453,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0454,)));
    __SET_VAR(data__->,CLX_0455,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0456,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0455,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0183_body__() 





void CLX_0169_init__(CLX_0169_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_SP,data__->LIT_2601_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_AUTO,data__->PMP_2001_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_ENABLE,data__->PMP_2001_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0457,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0458,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0459,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0460,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0461,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0462,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0169_body__(CLX_0169_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2001_ENABLE,) && __GET_EXTERNAL(data__->PMP_2001_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2601_SP,) - __GET_EXTERNAL(data__->LIT_2601,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0457,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0458,)) * __GET_VAR(data__->CLX_0460,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0459,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0460,)));
    __SET_VAR(data__->,CLX_0461,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0462,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0461,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0169_body__() 





void CLX_0171_init__(CLX_0171_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_SP,data__->LIT_2601_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_AUTO,data__->PMP_2002_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_ENABLE,data__->PMP_2002_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0463,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0464,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0465,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0466,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0467,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0468,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0171_body__(CLX_0171_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2002_ENABLE,) && __GET_EXTERNAL(data__->PMP_2002_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2601_SP,) - __GET_EXTERNAL(data__->LIT_2601,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0463,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0464,)) * __GET_VAR(data__->CLX_0466,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0465,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0466,)));
    __SET_VAR(data__->,CLX_0467,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0468,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0467,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0171_body__() 





void CLX_0173_init__(CLX_0173_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_SP,data__->LIT_2601_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_AUTO,data__->PMP_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_ENABLE,data__->PMP_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0469,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0470,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0471,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0472,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0473,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0474,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0173_body__(CLX_0173_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2201_ENABLE,) && __GET_EXTERNAL(data__->PMP_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2601_SP,) - __GET_EXTERNAL(data__->LIT_2601,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0469,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0470,)) * __GET_VAR(data__->CLX_0472,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0471,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0472,)));
    __SET_VAR(data__->,CLX_0473,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0474,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0473,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0173_body__() 





void CLX_0175_init__(CLX_0175_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_SP,data__->LIT_2601_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_AUTO,data__->PMP_2601_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_ENABLE,data__->PMP_2601_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0475,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0476,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0477,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0478,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0479,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0480,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0175_body__(CLX_0175_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2601_ENABLE,) && __GET_EXTERNAL(data__->PMP_2601_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2601_SP,) - __GET_EXTERNAL(data__->LIT_2601,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0475,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0476,)) * __GET_VAR(data__->CLX_0478,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0477,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0478,)));
    __SET_VAR(data__->,CLX_0479,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0480,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0479,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0175_body__() 





void CLX_0177_init__(CLX_0177_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_SP,data__->LIT_2601_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_AUTO,data__->PMP_2602_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_ENABLE,data__->PMP_2602_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0481,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0482,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0483,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0484,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0485,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0486,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0177_body__(CLX_0177_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2602_ENABLE,) && __GET_EXTERNAL(data__->PMP_2602_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2601_SP,) - __GET_EXTERNAL(data__->LIT_2601,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0481,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0482,)) * __GET_VAR(data__->CLX_0484,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0483,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0484,)));
    __SET_VAR(data__->,CLX_0485,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0486,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0485,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0177_body__() 





void CLX_0179_init__(CLX_0179_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_SP,data__->LIT_2601_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_AUTO,data__->PMP_4501_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_ENABLE,data__->PMP_4501_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0487,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0488,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0489,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0490,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0491,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0492,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0179_body__(CLX_0179_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4501_ENABLE,) && __GET_EXTERNAL(data__->PMP_4501_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2601_SP,) - __GET_EXTERNAL(data__->LIT_2601,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0487,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0488,)) * __GET_VAR(data__->CLX_0490,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0489,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0490,)));
    __SET_VAR(data__->,CLX_0491,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0492,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0491,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0179_body__() 





void CLX_0181_init__(CLX_0181_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_SP,data__->LIT_2601_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_AUTO,data__->PMP_4502_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_ENABLE,data__->PMP_4502_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0493,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0494,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0495,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0496,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0497,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0498,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0181_body__(CLX_0181_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4502_ENABLE,) && __GET_EXTERNAL(data__->PMP_4502_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LIT_2601_SP,) - __GET_EXTERNAL(data__->LIT_2601,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0493,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0494,)) * __GET_VAR(data__->CLX_0496,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0495,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0496,)));
    __SET_VAR(data__->,CLX_0497,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0498,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0497,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0181_body__() 





void CLX_0199_init__(CLX_0199_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(REAL,LSHH_2001_SP,data__->LSHH_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_AUTO,data__->P_20_AUTO,retain)
  __INIT_EXTERNAL(BOOL,P_20_ENABLE,data__->P_20_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0499,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0500,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0501,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0502,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0503,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0504,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0199_body__(CLX_0199_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->P_20_ENABLE,) && __GET_EXTERNAL(data__->P_20_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSHH_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSHH_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0499,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0500,)) * __GET_VAR(data__->CLX_0502,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0501,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0502,)));
    __SET_VAR(data__->,CLX_0503,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0504,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0503,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0199_body__() 





void CLX_0185_init__(CLX_0185_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(REAL,LSHH_2001_SP,data__->LSHH_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_AUTO,data__->PMP_2001_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_ENABLE,data__->PMP_2001_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0505,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0506,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0507,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0508,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0509,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0510,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0185_body__(CLX_0185_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2001_ENABLE,) && __GET_EXTERNAL(data__->PMP_2001_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSHH_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSHH_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0505,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0506,)) * __GET_VAR(data__->CLX_0508,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0507,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0508,)));
    __SET_VAR(data__->,CLX_0509,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0510,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0509,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0185_body__() 





void CLX_0187_init__(CLX_0187_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(REAL,LSHH_2001_SP,data__->LSHH_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_AUTO,data__->PMP_2002_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_ENABLE,data__->PMP_2002_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0511,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0512,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0513,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0514,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0515,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0516,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0187_body__(CLX_0187_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2002_ENABLE,) && __GET_EXTERNAL(data__->PMP_2002_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSHH_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSHH_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0511,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0512,)) * __GET_VAR(data__->CLX_0514,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0513,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0514,)));
    __SET_VAR(data__->,CLX_0515,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0516,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0515,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0187_body__() 





void CLX_0189_init__(CLX_0189_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(REAL,LSHH_2001_SP,data__->LSHH_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_AUTO,data__->PMP_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_ENABLE,data__->PMP_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0517,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0518,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0519,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0520,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0521,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0522,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0189_body__(CLX_0189_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2201_ENABLE,) && __GET_EXTERNAL(data__->PMP_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSHH_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSHH_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0517,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0518,)) * __GET_VAR(data__->CLX_0520,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0519,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0520,)));
    __SET_VAR(data__->,CLX_0521,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0522,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0521,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0189_body__() 





void CLX_0191_init__(CLX_0191_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(REAL,LSHH_2001_SP,data__->LSHH_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_AUTO,data__->PMP_2601_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_ENABLE,data__->PMP_2601_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0523,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0524,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0525,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0526,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0527,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0528,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0191_body__(CLX_0191_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2601_ENABLE,) && __GET_EXTERNAL(data__->PMP_2601_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSHH_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSHH_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0523,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0524,)) * __GET_VAR(data__->CLX_0526,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0525,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0526,)));
    __SET_VAR(data__->,CLX_0527,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0528,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0527,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0191_body__() 





void CLX_0193_init__(CLX_0193_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(REAL,LSHH_2001_SP,data__->LSHH_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_AUTO,data__->PMP_2602_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_ENABLE,data__->PMP_2602_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0529,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0530,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0531,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0532,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0533,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0534,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0193_body__(CLX_0193_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2602_ENABLE,) && __GET_EXTERNAL(data__->PMP_2602_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSHH_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSHH_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0529,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0530,)) * __GET_VAR(data__->CLX_0532,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0531,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0532,)));
    __SET_VAR(data__->,CLX_0533,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0534,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0533,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0193_body__() 





void CLX_0195_init__(CLX_0195_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(REAL,LSHH_2001_SP,data__->LSHH_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_AUTO,data__->PMP_4501_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_ENABLE,data__->PMP_4501_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0535,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0536,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0537,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0538,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0539,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0540,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0195_body__(CLX_0195_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4501_ENABLE,) && __GET_EXTERNAL(data__->PMP_4501_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSHH_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSHH_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0535,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0536,)) * __GET_VAR(data__->CLX_0538,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0537,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0538,)));
    __SET_VAR(data__->,CLX_0539,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0540,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0539,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0195_body__() 





void CLX_0197_init__(CLX_0197_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(REAL,LSHH_2001_SP,data__->LSHH_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_AUTO,data__->PMP_4502_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_ENABLE,data__->PMP_4502_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0541,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0542,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0543,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0544,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0545,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0546,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0197_body__(CLX_0197_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4502_ENABLE,) && __GET_EXTERNAL(data__->PMP_4502_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSHH_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSHH_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0541,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0542,)) * __GET_VAR(data__->CLX_0544,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0543,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0544,)));
    __SET_VAR(data__->,CLX_0545,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0546,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0545,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0197_body__() 





void CLX_0215_init__(CLX_0215_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(REAL,LSLL_2001_SP,data__->LSLL_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_AUTO,data__->P_20_AUTO,retain)
  __INIT_EXTERNAL(BOOL,P_20_ENABLE,data__->P_20_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0547,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0548,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0549,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0550,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0551,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0552,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0215_body__(CLX_0215_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->P_20_ENABLE,) && __GET_EXTERNAL(data__->P_20_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSLL_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSLL_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0547,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0548,)) * __GET_VAR(data__->CLX_0550,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0549,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0550,)));
    __SET_VAR(data__->,CLX_0551,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0552,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0551,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0215_body__() 





void CLX_0201_init__(CLX_0201_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(REAL,LSLL_2001_SP,data__->LSLL_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_AUTO,data__->PMP_2001_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_ENABLE,data__->PMP_2001_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0553,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0554,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0555,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0556,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0557,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0558,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0201_body__(CLX_0201_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2001_ENABLE,) && __GET_EXTERNAL(data__->PMP_2001_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSLL_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSLL_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0553,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0554,)) * __GET_VAR(data__->CLX_0556,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0555,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0556,)));
    __SET_VAR(data__->,CLX_0557,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0558,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0557,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0201_body__() 





void CLX_0203_init__(CLX_0203_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(REAL,LSLL_2001_SP,data__->LSLL_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_AUTO,data__->PMP_2002_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_ENABLE,data__->PMP_2002_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0559,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0560,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0561,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0562,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0563,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0564,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0203_body__(CLX_0203_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2002_ENABLE,) && __GET_EXTERNAL(data__->PMP_2002_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSLL_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSLL_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0559,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0560,)) * __GET_VAR(data__->CLX_0562,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0561,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0562,)));
    __SET_VAR(data__->,CLX_0563,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0564,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0563,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0203_body__() 





void CLX_0205_init__(CLX_0205_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(REAL,LSLL_2001_SP,data__->LSLL_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_AUTO,data__->PMP_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_ENABLE,data__->PMP_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0565,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0566,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0567,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0568,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0569,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0570,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0205_body__(CLX_0205_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2201_ENABLE,) && __GET_EXTERNAL(data__->PMP_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSLL_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSLL_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0565,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0566,)) * __GET_VAR(data__->CLX_0568,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0567,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0568,)));
    __SET_VAR(data__->,CLX_0569,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0570,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0569,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0205_body__() 





void CLX_0207_init__(CLX_0207_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(REAL,LSLL_2001_SP,data__->LSLL_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_AUTO,data__->PMP_2601_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_ENABLE,data__->PMP_2601_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0571,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0572,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0573,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0574,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0575,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0576,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0207_body__(CLX_0207_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2601_ENABLE,) && __GET_EXTERNAL(data__->PMP_2601_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSLL_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSLL_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0571,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0572,)) * __GET_VAR(data__->CLX_0574,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0573,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0574,)));
    __SET_VAR(data__->,CLX_0575,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0576,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0575,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0207_body__() 





void CLX_0209_init__(CLX_0209_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(REAL,LSLL_2001_SP,data__->LSLL_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_AUTO,data__->PMP_2602_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_ENABLE,data__->PMP_2602_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0577,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0578,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0579,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0580,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0581,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0582,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0209_body__(CLX_0209_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_2602_ENABLE,) && __GET_EXTERNAL(data__->PMP_2602_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSLL_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSLL_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0577,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0578,)) * __GET_VAR(data__->CLX_0580,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0579,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0580,)));
    __SET_VAR(data__->,CLX_0581,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0582,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0581,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0209_body__() 





void CLX_0211_init__(CLX_0211_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(REAL,LSLL_2001_SP,data__->LSLL_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_AUTO,data__->PMP_4501_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_ENABLE,data__->PMP_4501_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0583,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0584,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0585,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0586,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0587,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0588,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0211_body__(CLX_0211_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4501_ENABLE,) && __GET_EXTERNAL(data__->PMP_4501_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSLL_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSLL_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0583,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0584,)) * __GET_VAR(data__->CLX_0586,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0585,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0586,)));
    __SET_VAR(data__->,CLX_0587,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0588,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0587,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0211_body__() 





void CLX_0213_init__(CLX_0213_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(REAL,LSLL_2001_SP,data__->LSLL_2001_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_AUTO,data__->PMP_4502_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_ENABLE,data__->PMP_4502_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0589,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0590,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0591,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0592,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0593,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0594,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0213_body__(CLX_0213_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->PMP_4502_ENABLE,) && __GET_EXTERNAL(data__->PMP_4502_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->LSLL_2001_SP,) - ___BOOL_TO_REAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (BOOL)__GET_EXTERNAL(data__->LSLL_2001,))));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0589,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0590,)) * __GET_VAR(data__->CLX_0592,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0591,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0592,)));
    __SET_VAR(data__->,CLX_0593,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0594,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0593,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0213_body__() 





void CLX_0217_init__(CLX_0217_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_AUTO,data__->FCV_2301_AUTO,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_ENABLE,data__->FCV_2301_ENABLE,retain)
  __INIT_EXTERNAL(REAL,PIT_4001,data__->PIT_4001,retain)
  __INIT_EXTERNAL(REAL,PIT_4001_SP,data__->PIT_4001_SP,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0595,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0596,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0597,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0598,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0599,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0600,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0217_body__(CLX_0217_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->FCV_2301_ENABLE,) && __GET_EXTERNAL(data__->FCV_2301_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->PIT_4001_SP,) - __GET_EXTERNAL(data__->PIT_4001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0595,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0596,)) * __GET_VAR(data__->CLX_0598,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0597,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0598,)));
    __SET_VAR(data__->,CLX_0599,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0600,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0599,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0217_body__() 





void CLX_0219_init__(CLX_0219_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,PIT_4001,data__->PIT_4001,retain)
  __INIT_EXTERNAL(REAL,PIT_4001_SP,data__->PIT_4001_SP,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_AUTO,data__->VAL_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_ENABLE,data__->VAL_2201_ENABLE,retain)
  __INIT_VAR(data__->CLX_0277,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0278,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0279,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0280,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0281,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0282,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0601,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0602,__REAL_LITERAL(0.1),retain)
  __INIT_VAR(data__->CLX_0603,__REAL_LITERAL(0.01),retain)
  __INIT_VAR(data__->CLX_0604,__REAL_LITERAL(1.0),retain)
  __INIT_VAR(data__->CLX_0605,__REAL_LITERAL(0.0),retain)
  __INIT_VAR(data__->CLX_0606,__REAL_LITERAL(0.0),retain)
}

// Code part
void CLX_0219_body__(CLX_0219_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->VAL_2201_ENABLE,) && __GET_EXTERNAL(data__->VAL_2201_AUTO,))) {
    __SET_VAR(data__->,CLX_0277,,(__GET_EXTERNAL(data__->PIT_4001_SP,) - __GET_EXTERNAL(data__->PIT_4001,)));
    __SET_VAR(data__->,CLX_0278,,(__GET_VAR(data__->CLX_0601,) * __GET_VAR(data__->CLX_0277,)));
    __SET_VAR(data__->,CLX_0282,,(__GET_VAR(data__->CLX_0282,) + ((__GET_VAR(data__->CLX_0277,) * __GET_VAR(data__->CLX_0602,)) * __GET_VAR(data__->CLX_0604,))));
    __SET_VAR(data__->,CLX_0279,,__GET_VAR(data__->CLX_0282,));
    __SET_VAR(data__->,CLX_0280,,((__GET_VAR(data__->CLX_0603,) * (__GET_VAR(data__->CLX_0277,) - __GET_VAR(data__->CLX_0281,))) / __GET_VAR(data__->CLX_0604,)));
    __SET_VAR(data__->,CLX_0605,,((__GET_VAR(data__->CLX_0278,) + __GET_VAR(data__->CLX_0279,)) + __GET_VAR(data__->CLX_0280,)));
    __SET_VAR(data__->,CLX_0606,,___CLX_CLAMPREAL(
      (BOOL)__BOOL_LITERAL(TRUE),
      NULL,
      (REAL)__GET_VAR(data__->CLX_0605,),
      (REAL)__REAL_LITERAL(0.0),
      (REAL)__REAL_LITERAL(100.0)));
    __SET_VAR(data__->,CLX_0281,,__GET_VAR(data__->CLX_0277,));
  };

  goto __end;

__end:
  return;
} // CLX_0219_body__() 





void FB_EQ_BL_4001_init__(FB_EQ_BL_4001_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,BL_4001_AUTO,data__->BL_4001_AUTO,retain)
  __INIT_EXTERNAL(BOOL,BL_4001_CMD,data__->BL_4001_CMD,retain)
  __INIT_EXTERNAL(BOOL,BL_4001_FAULT,data__->BL_4001_FAULT,retain)
  __INIT_EXTERNAL(BOOL,BL_4001_PERMISSIVE,data__->BL_4001_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,BL_4001_RUN_CMD,data__->BL_4001_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,BL_4001_RUN_FB,data__->BL_4001_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,BL_4001_STATUS,data__->BL_4001_STATUS,retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_VAR(data__->CMD_VALID_BL_4001,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0607,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FAULT_ACTIVE_BL_4001,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_BL_4001,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0608,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0609,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_BL_4001_body__(FB_EQ_BL_4001_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0609,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0609,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0609,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0609,)) {
    __SET_VAR(data__->,CMD_VALID_BL_4001,,__GET_EXTERNAL(data__->BL_4001_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_BL_4001,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0607,,__GET_EXTERNAL(data__->BL_4001_PERMISSIVE,));
  __SET_VAR(data__->,FAULT_ACTIVE_BL_4001,,__GET_EXTERNAL(data__->BL_4001_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_BL_4001,,__GET_EXTERNAL(data__->BL_4001_AUTO,));
  __SET_VAR(data__->,CLX_0608,,__GET_EXTERNAL(data__->BL_4001_RUN_FB,));
  if (__GET_VAR(data__->FAULT_ACTIVE_BL_4001,)) {
    __SET_EXTERNAL(data__->,BL_4001_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,BL_4001_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_BL_4001,)) {
    if (__GET_VAR(data__->CLX_0607,)) {
      if (__GET_VAR(data__->CMD_VALID_BL_4001,)) {
        __SET_EXTERNAL(data__->,BL_4001_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0608,)) {
          __SET_EXTERNAL(data__->,BL_4001_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,BL_4001_STATUS,,__GET_EXTERNAL(data__->BL_4001_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,BL_4001_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,BL_4001_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,BL_4001_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,BL_4001_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,BL_4001_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,BL_4001_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_BL_4001_body__() 





void FB_EQ_BL_4002_init__(FB_EQ_BL_4002_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,BL_4002_AUTO,data__->BL_4002_AUTO,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_CMD,data__->BL_4002_CMD,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_FAULT,data__->BL_4002_FAULT,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_PERMISSIVE,data__->BL_4002_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_RUN_CMD,data__->BL_4002_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_RUN_FB,data__->BL_4002_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_STATUS,data__->BL_4002_STATUS,retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_VAR(data__->CMD_VALID_BL_4002,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0610,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FAULT_ACTIVE_BL_4002,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_BL_4002,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0611,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0612,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_BL_4002_body__(FB_EQ_BL_4002_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0612,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0612,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0612,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0612,)) {
    __SET_VAR(data__->,CMD_VALID_BL_4002,,__GET_EXTERNAL(data__->BL_4002_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_BL_4002,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0610,,__GET_EXTERNAL(data__->BL_4002_PERMISSIVE,));
  __SET_VAR(data__->,FAULT_ACTIVE_BL_4002,,__GET_EXTERNAL(data__->BL_4002_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_BL_4002,,__GET_EXTERNAL(data__->BL_4002_AUTO,));
  __SET_VAR(data__->,CLX_0611,,__GET_EXTERNAL(data__->BL_4002_RUN_FB,));
  if (__GET_VAR(data__->FAULT_ACTIVE_BL_4002,)) {
    __SET_EXTERNAL(data__->,BL_4002_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,BL_4002_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_BL_4002,)) {
    if (__GET_VAR(data__->CLX_0610,)) {
      if (__GET_VAR(data__->CMD_VALID_BL_4002,)) {
        __SET_EXTERNAL(data__->,BL_4002_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0611,)) {
          __SET_EXTERNAL(data__->,BL_4002_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,BL_4002_STATUS,,__GET_EXTERNAL(data__->BL_4002_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,BL_4002_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,BL_4002_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,BL_4002_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,BL_4002_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,BL_4002_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,BL_4002_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_BL_4002_body__() 





void FB_EQ_FCV_2301_init__(FB_EQ_FCV_2301_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_AUTO,data__->FCV_2301_AUTO,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_CLOSE_CMD,data__->FCV_2301_CLOSE_CMD,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_FAULT,data__->FCV_2301_FAULT,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_MANUAL,data__->FCV_2301_MANUAL,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_OPEN_CMD,data__->FCV_2301_OPEN_CMD,retain)
  __INIT_EXTERNAL(REAL,FCV_2301_OUT,data__->FCV_2301_OUT,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_PERMISSIVE,data__->FCV_2301_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_RUN_FB,data__->FCV_2301_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_STATUS,data__->FCV_2301_STATUS,retain)
  __INIT_VAR(data__->CLX_0613,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0614,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_FCV_2301,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0615,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OPEN_ACTIVE_FCV_2301,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0616,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0617,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0618,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_FCV_2301_body__(FB_EQ_FCV_2301_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0618,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0618,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0618,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0613,,__GET_EXTERNAL(data__->FCV_2301_FAULT,));
  __SET_VAR(data__->,CLX_0614,,__GET_EXTERNAL(data__->FCV_2301_PERMISSIVE,));
  __SET_VAR(data__->,AUTO_ACTIVE_FCV_2301,,__GET_EXTERNAL(data__->FCV_2301_AUTO,));
  __SET_VAR(data__->,CLX_0615,,__GET_EXTERNAL(data__->FCV_2301_MANUAL,));
  if (__GET_VAR(data__->CLX_0618,)) {
    __SET_VAR(data__->,OPEN_ACTIVE_FCV_2301,,__GET_EXTERNAL(data__->FCV_2301_OPEN_CMD,));
    __SET_VAR(data__->,CLX_0616,,__GET_EXTERNAL(data__->FCV_2301_CLOSE_CMD,));
  } else {
    __SET_VAR(data__->,OPEN_ACTIVE_FCV_2301,,__BOOL_LITERAL(FALSE));
    __SET_VAR(data__->,CLX_0616,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0617,,(__GET_EXTERNAL(data__->FCV_2301_OUT,) > __REAL_LITERAL(0.1)));
  if (__GET_VAR(data__->CLX_0613,)) {
    __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (!(__GET_VAR(data__->CLX_0618,))) {
    __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (!(__GET_VAR(data__->CLX_0614,))) {
    __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_FCV_2301,)) {
    if (__GET_VAR(data__->CLX_0617,)) {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(TRUE));
    } else if (__GET_EXTERNAL(data__->FCV_2301_RUN_FB,)) {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(TRUE));
    } else {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else if (__GET_VAR(data__->CLX_0615,)) {
    __SET_VAR(data__->,CLX_0617,,(__GET_EXTERNAL(data__->FCV_2301_OUT,) > __REAL_LITERAL(0.1)));
    if (__GET_VAR(data__->CLX_0617,)) {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(TRUE));
    } else if (__GET_EXTERNAL(data__->FCV_2301_RUN_FB,)) {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(TRUE));
    } else {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_VAR(data__->,CLX_0617,,(__GET_EXTERNAL(data__->FCV_2301_OUT,) > __REAL_LITERAL(0.1)));
    if (__GET_VAR(data__->CLX_0617,)) {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(TRUE));
    } else if (__GET_EXTERNAL(data__->FCV_2301_RUN_FB,)) {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(TRUE));
    } else {
      __SET_EXTERNAL(data__->,FCV_2301_STATUS,,__BOOL_LITERAL(FALSE));
    };
  };

  goto __end;

__end:
  return;
} // FB_EQ_FCV_2301_body__() 





void FB_EQ_P_20_init__(FB_EQ_P_20_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,P_20_AUTO,data__->P_20_AUTO,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_EXTERNAL(BOOL,P_20_FAULT,data__->P_20_FAULT,retain)
  __INIT_EXTERNAL(BOOL,P_20_PERMISSIVE,data__->P_20_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,P_20_RUN_CMD,data__->P_20_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,P_20_RUN_FB,data__->P_20_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,P_20_STATUS,data__->P_20_STATUS,retain)
  __INIT_VAR(data__->CMD_VALID_P_20,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->PERMISSIVE_OK_P_20,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->FAULT_ACTIVE_P_20,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_P_20,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0619,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0620,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_P_20_body__(FB_EQ_P_20_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0620,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0620,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0620,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0620,)) {
    __SET_VAR(data__->,CMD_VALID_P_20,,__GET_EXTERNAL(data__->P_20_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_P_20,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,PERMISSIVE_OK_P_20,,__GET_EXTERNAL(data__->P_20_PERMISSIVE,));
  __SET_VAR(data__->,FAULT_ACTIVE_P_20,,__GET_EXTERNAL(data__->P_20_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_P_20,,__GET_EXTERNAL(data__->P_20_AUTO,));
  __SET_VAR(data__->,CLX_0619,,__GET_EXTERNAL(data__->P_20_RUN_FB,));
  if (__GET_VAR(data__->FAULT_ACTIVE_P_20,)) {
    __SET_EXTERNAL(data__->,P_20_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,P_20_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_P_20,)) {
    if (__GET_VAR(data__->PERMISSIVE_OK_P_20,)) {
      if (__GET_VAR(data__->CMD_VALID_P_20,)) {
        __SET_EXTERNAL(data__->,P_20_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0619,)) {
          __SET_EXTERNAL(data__->,P_20_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,P_20_STATUS,,__GET_EXTERNAL(data__->P_20_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,P_20_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,P_20_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,P_20_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,P_20_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,P_20_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,P_20_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_P_20_body__() 





void FB_EQ_PMP_2001_init__(FB_EQ_PMP_2001_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_AUTO,data__->PMP_2001_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_FAULT,data__->PMP_2001_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_PERMISSIVE,data__->PMP_2001_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_RUN_CMD,data__->PMP_2001_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_RUN_FB,data__->PMP_2001_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_STATUS,data__->PMP_2001_STATUS,retain)
  __INIT_VAR(data__->CMD_VALID_PMP_2001,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0621,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0622,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_PMP_2001,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0623,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0624,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_PMP_2001_body__(FB_EQ_PMP_2001_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0624,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0624,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0624,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0624,)) {
    __SET_VAR(data__->,CMD_VALID_PMP_2001,,__GET_EXTERNAL(data__->PMP_2001_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_PMP_2001,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0621,,__GET_EXTERNAL(data__->PMP_2001_PERMISSIVE,));
  __SET_VAR(data__->,CLX_0622,,__GET_EXTERNAL(data__->PMP_2001_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_PMP_2001,,__GET_EXTERNAL(data__->PMP_2001_AUTO,));
  __SET_VAR(data__->,CLX_0623,,__GET_EXTERNAL(data__->PMP_2001_RUN_FB,));
  if (__GET_VAR(data__->CLX_0622,)) {
    __SET_EXTERNAL(data__->,PMP_2001_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2001_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_PMP_2001,)) {
    if (__GET_VAR(data__->CLX_0621,)) {
      if (__GET_VAR(data__->CMD_VALID_PMP_2001,)) {
        __SET_EXTERNAL(data__->,PMP_2001_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0623,)) {
          __SET_EXTERNAL(data__->,PMP_2001_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,PMP_2001_STATUS,,__GET_EXTERNAL(data__->PMP_2001_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,PMP_2001_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,PMP_2001_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,PMP_2001_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,PMP_2001_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,PMP_2001_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2001_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_PMP_2001_body__() 





void FB_EQ_PMP_2002_init__(FB_EQ_PMP_2002_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_AUTO,data__->PMP_2002_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_FAULT,data__->PMP_2002_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_PERMISSIVE,data__->PMP_2002_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_RUN_CMD,data__->PMP_2002_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_RUN_FB,data__->PMP_2002_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_STATUS,data__->PMP_2002_STATUS,retain)
  __INIT_VAR(data__->CMD_VALID_PMP_2002,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0625,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0626,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_PMP_2002,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0627,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0628,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_PMP_2002_body__(FB_EQ_PMP_2002_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0628,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0628,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0628,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0628,)) {
    __SET_VAR(data__->,CMD_VALID_PMP_2002,,__GET_EXTERNAL(data__->PMP_2002_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_PMP_2002,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0625,,__GET_EXTERNAL(data__->PMP_2002_PERMISSIVE,));
  __SET_VAR(data__->,CLX_0626,,__GET_EXTERNAL(data__->PMP_2002_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_PMP_2002,,__GET_EXTERNAL(data__->PMP_2002_AUTO,));
  __SET_VAR(data__->,CLX_0627,,__GET_EXTERNAL(data__->PMP_2002_RUN_FB,));
  if (__GET_VAR(data__->CLX_0626,)) {
    __SET_EXTERNAL(data__->,PMP_2002_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2002_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_PMP_2002,)) {
    if (__GET_VAR(data__->CLX_0625,)) {
      if (__GET_VAR(data__->CMD_VALID_PMP_2002,)) {
        __SET_EXTERNAL(data__->,PMP_2002_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0627,)) {
          __SET_EXTERNAL(data__->,PMP_2002_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,PMP_2002_STATUS,,__GET_EXTERNAL(data__->PMP_2002_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,PMP_2002_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,PMP_2002_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,PMP_2002_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,PMP_2002_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,PMP_2002_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2002_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_PMP_2002_body__() 





void FB_EQ_PMP_2201_init__(FB_EQ_PMP_2201_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_AUTO,data__->PMP_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_FAULT,data__->PMP_2201_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_PERMISSIVE,data__->PMP_2201_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_RUN_CMD,data__->PMP_2201_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_RUN_FB,data__->PMP_2201_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_STATUS,data__->PMP_2201_STATUS,retain)
  __INIT_VAR(data__->CMD_VALID_PMP_2201,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0629,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0630,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_PMP_2201,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0631,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0632,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_PMP_2201_body__(FB_EQ_PMP_2201_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0632,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0632,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0632,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0632,)) {
    __SET_VAR(data__->,CMD_VALID_PMP_2201,,__GET_EXTERNAL(data__->PMP_2201_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_PMP_2201,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0629,,__GET_EXTERNAL(data__->PMP_2201_PERMISSIVE,));
  __SET_VAR(data__->,CLX_0630,,__GET_EXTERNAL(data__->PMP_2201_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_PMP_2201,,__GET_EXTERNAL(data__->PMP_2201_AUTO,));
  __SET_VAR(data__->,CLX_0631,,__GET_EXTERNAL(data__->PMP_2201_RUN_FB,));
  if (__GET_VAR(data__->CLX_0630,)) {
    __SET_EXTERNAL(data__->,PMP_2201_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2201_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_PMP_2201,)) {
    if (__GET_VAR(data__->CLX_0629,)) {
      if (__GET_VAR(data__->CMD_VALID_PMP_2201,)) {
        __SET_EXTERNAL(data__->,PMP_2201_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0631,)) {
          __SET_EXTERNAL(data__->,PMP_2201_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,PMP_2201_STATUS,,__GET_EXTERNAL(data__->PMP_2201_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,PMP_2201_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,PMP_2201_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,PMP_2201_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,PMP_2201_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,PMP_2201_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2201_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_PMP_2201_body__() 





void FB_EQ_PMP_2601_init__(FB_EQ_PMP_2601_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_AUTO,data__->PMP_2601_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_FAULT,data__->PMP_2601_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_PERMISSIVE,data__->PMP_2601_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_RUN_CMD,data__->PMP_2601_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_RUN_FB,data__->PMP_2601_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_STATUS,data__->PMP_2601_STATUS,retain)
  __INIT_VAR(data__->CMD_VALID_PMP_2601,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0633,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0634,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_PMP_2601,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0635,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0636,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_PMP_2601_body__(FB_EQ_PMP_2601_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0636,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0636,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0636,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0636,)) {
    __SET_VAR(data__->,CMD_VALID_PMP_2601,,__GET_EXTERNAL(data__->PMP_2601_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_PMP_2601,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0633,,__GET_EXTERNAL(data__->PMP_2601_PERMISSIVE,));
  __SET_VAR(data__->,CLX_0634,,__GET_EXTERNAL(data__->PMP_2601_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_PMP_2601,,__GET_EXTERNAL(data__->PMP_2601_AUTO,));
  __SET_VAR(data__->,CLX_0635,,__GET_EXTERNAL(data__->PMP_2601_RUN_FB,));
  if (__GET_VAR(data__->CLX_0634,)) {
    __SET_EXTERNAL(data__->,PMP_2601_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2601_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_PMP_2601,)) {
    if (__GET_VAR(data__->CLX_0633,)) {
      if (__GET_VAR(data__->CMD_VALID_PMP_2601,)) {
        __SET_EXTERNAL(data__->,PMP_2601_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0635,)) {
          __SET_EXTERNAL(data__->,PMP_2601_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,PMP_2601_STATUS,,__GET_EXTERNAL(data__->PMP_2601_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,PMP_2601_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,PMP_2601_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,PMP_2601_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,PMP_2601_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,PMP_2601_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2601_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_PMP_2601_body__() 





void FB_EQ_PMP_2602_init__(FB_EQ_PMP_2602_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_AUTO,data__->PMP_2602_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_FAULT,data__->PMP_2602_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_PERMISSIVE,data__->PMP_2602_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_RUN_CMD,data__->PMP_2602_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_RUN_FB,data__->PMP_2602_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_STATUS,data__->PMP_2602_STATUS,retain)
  __INIT_VAR(data__->CMD_VALID_PMP_2602,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0637,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0638,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_PMP_2602,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0639,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0640,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_PMP_2602_body__(FB_EQ_PMP_2602_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0640,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0640,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0640,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0640,)) {
    __SET_VAR(data__->,CMD_VALID_PMP_2602,,__GET_EXTERNAL(data__->PMP_2602_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_PMP_2602,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0637,,__GET_EXTERNAL(data__->PMP_2602_PERMISSIVE,));
  __SET_VAR(data__->,CLX_0638,,__GET_EXTERNAL(data__->PMP_2602_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_PMP_2602,,__GET_EXTERNAL(data__->PMP_2602_AUTO,));
  __SET_VAR(data__->,CLX_0639,,__GET_EXTERNAL(data__->PMP_2602_RUN_FB,));
  if (__GET_VAR(data__->CLX_0638,)) {
    __SET_EXTERNAL(data__->,PMP_2602_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2602_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_PMP_2602,)) {
    if (__GET_VAR(data__->CLX_0637,)) {
      if (__GET_VAR(data__->CMD_VALID_PMP_2602,)) {
        __SET_EXTERNAL(data__->,PMP_2602_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0639,)) {
          __SET_EXTERNAL(data__->,PMP_2602_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,PMP_2602_STATUS,,__GET_EXTERNAL(data__->PMP_2602_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,PMP_2602_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,PMP_2602_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,PMP_2602_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,PMP_2602_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,PMP_2602_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_2602_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_PMP_2602_body__() 





void FB_EQ_PMP_4501_init__(FB_EQ_PMP_4501_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_AUTO,data__->PMP_4501_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_FAULT,data__->PMP_4501_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_PERMISSIVE,data__->PMP_4501_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_RUN_CMD,data__->PMP_4501_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_RUN_FB,data__->PMP_4501_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_STATUS,data__->PMP_4501_STATUS,retain)
  __INIT_VAR(data__->CMD_VALID_PMP_4501,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0641,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0642,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_PMP_4501,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0643,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0644,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_PMP_4501_body__(FB_EQ_PMP_4501_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0644,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0644,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0644,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0644,)) {
    __SET_VAR(data__->,CMD_VALID_PMP_4501,,__GET_EXTERNAL(data__->PMP_4501_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_PMP_4501,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0641,,__GET_EXTERNAL(data__->PMP_4501_PERMISSIVE,));
  __SET_VAR(data__->,CLX_0642,,__GET_EXTERNAL(data__->PMP_4501_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_PMP_4501,,__GET_EXTERNAL(data__->PMP_4501_AUTO,));
  __SET_VAR(data__->,CLX_0643,,__GET_EXTERNAL(data__->PMP_4501_RUN_FB,));
  if (__GET_VAR(data__->CLX_0642,)) {
    __SET_EXTERNAL(data__->,PMP_4501_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_4501_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_PMP_4501,)) {
    if (__GET_VAR(data__->CLX_0641,)) {
      if (__GET_VAR(data__->CMD_VALID_PMP_4501,)) {
        __SET_EXTERNAL(data__->,PMP_4501_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0643,)) {
          __SET_EXTERNAL(data__->,PMP_4501_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,PMP_4501_STATUS,,__GET_EXTERNAL(data__->PMP_4501_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,PMP_4501_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,PMP_4501_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,PMP_4501_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,PMP_4501_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,PMP_4501_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_4501_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_PMP_4501_body__() 





void FB_EQ_PMP_4502_init__(FB_EQ_PMP_4502_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_AUTO,data__->PMP_4502_AUTO,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_FAULT,data__->PMP_4502_FAULT,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_PERMISSIVE,data__->PMP_4502_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_RUN_CMD,data__->PMP_4502_RUN_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_RUN_FB,data__->PMP_4502_RUN_FB,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_STATUS,data__->PMP_4502_STATUS,retain)
  __INIT_VAR(data__->CMD_VALID_PMP_4502,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0645,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0646,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_PMP_4502,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0647,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0648,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_PMP_4502_body__(FB_EQ_PMP_4502_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0648,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0648,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0648,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0648,)) {
    __SET_VAR(data__->,CMD_VALID_PMP_4502,,__GET_EXTERNAL(data__->PMP_4502_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_PMP_4502,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0645,,__GET_EXTERNAL(data__->PMP_4502_PERMISSIVE,));
  __SET_VAR(data__->,CLX_0646,,__GET_EXTERNAL(data__->PMP_4502_FAULT,));
  __SET_VAR(data__->,AUTO_ACTIVE_PMP_4502,,__GET_EXTERNAL(data__->PMP_4502_AUTO,));
  __SET_VAR(data__->,CLX_0647,,__GET_EXTERNAL(data__->PMP_4502_RUN_FB,));
  if (__GET_VAR(data__->CLX_0646,)) {
    __SET_EXTERNAL(data__->,PMP_4502_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_4502_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_PMP_4502,)) {
    if (__GET_VAR(data__->CLX_0645,)) {
      if (__GET_VAR(data__->CMD_VALID_PMP_4502,)) {
        __SET_EXTERNAL(data__->,PMP_4502_RUN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_VAR(data__->CLX_0647,)) {
          __SET_EXTERNAL(data__->,PMP_4502_STATUS,,__BOOL_LITERAL(TRUE));
        } else {
          __SET_EXTERNAL(data__->,PMP_4502_STATUS,,__GET_EXTERNAL(data__->PMP_4502_RUN_CMD,));
        };
      } else {
        __SET_EXTERNAL(data__->,PMP_4502_RUN_CMD,,__BOOL_LITERAL(FALSE));
        __SET_EXTERNAL(data__->,PMP_4502_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,PMP_4502_RUN_CMD,,__BOOL_LITERAL(FALSE));
      __SET_EXTERNAL(data__->,PMP_4502_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,PMP_4502_RUN_CMD,,__BOOL_LITERAL(FALSE));
    __SET_EXTERNAL(data__->,PMP_4502_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_PMP_4502_body__() 





void FB_EQ_VAL_2201_init__(FB_EQ_VAL_2201_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_AUTO,data__->VAL_2201_AUTO,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_CLOSE_CMD,data__->VAL_2201_CLOSE_CMD,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_CMD,data__->VAL_2201_CMD,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_FAULT,data__->VAL_2201_FAULT,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_OPEN_CMD,data__->VAL_2201_OPEN_CMD,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_PERMISSIVE,data__->VAL_2201_PERMISSIVE,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_STATUS,data__->VAL_2201_STATUS,retain)
  __INIT_VAR(data__->CLX_0649,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0650,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->AUTO_ACTIVE_VAL_2201,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CMD_VALID_VAL_2201,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->OPEN_ACTIVE_VAL_2201,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0651,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->CLX_0652,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_EQ_VAL_2201_body__(FB_EQ_VAL_2201_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_RUNNING)) {
    __SET_VAR(data__->,CLX_0652,,__BOOL_LITERAL(TRUE));
  } else if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) == PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,CLX_0652,,__BOOL_LITERAL(TRUE));
  } else {
    __SET_VAR(data__->,CLX_0652,,__BOOL_LITERAL(FALSE));
  };
  __SET_VAR(data__->,CLX_0649,,__GET_EXTERNAL(data__->VAL_2201_FAULT,));
  __SET_VAR(data__->,CLX_0650,,__GET_EXTERNAL(data__->VAL_2201_PERMISSIVE,));
  __SET_VAR(data__->,AUTO_ACTIVE_VAL_2201,,__GET_EXTERNAL(data__->VAL_2201_AUTO,));
  if (__GET_VAR(data__->CLX_0652,)) {
    __SET_VAR(data__->,CMD_VALID_VAL_2201,,__GET_EXTERNAL(data__->VAL_2201_CMD,));
    __SET_VAR(data__->,OPEN_ACTIVE_VAL_2201,,__GET_EXTERNAL(data__->VAL_2201_OPEN_CMD,));
    __SET_VAR(data__->,CLX_0651,,__GET_EXTERNAL(data__->VAL_2201_CLOSE_CMD,));
  } else {
    __SET_VAR(data__->,CMD_VALID_VAL_2201,,__BOOL_LITERAL(FALSE));
    __SET_VAR(data__->,OPEN_ACTIVE_VAL_2201,,__BOOL_LITERAL(FALSE));
    __SET_VAR(data__->,CLX_0651,,__BOOL_LITERAL(FALSE));
  };
  if (__GET_VAR(data__->CLX_0649,)) {
    __SET_EXTERNAL(data__->,VAL_2201_STATUS,,__BOOL_LITERAL(FALSE));
  } else if (__GET_VAR(data__->AUTO_ACTIVE_VAL_2201,)) {
    if (__GET_VAR(data__->CLX_0650,)) {
      if (__GET_VAR(data__->OPEN_ACTIVE_VAL_2201,)) {
        __SET_EXTERNAL(data__->,VAL_2201_STATUS,,__BOOL_LITERAL(TRUE));
      } else if (__GET_VAR(data__->CMD_VALID_VAL_2201,)) {
        __SET_EXTERNAL(data__->,VAL_2201_STATUS,,__BOOL_LITERAL(TRUE));
      } else if (__GET_VAR(data__->CLX_0651,)) {
        __SET_EXTERNAL(data__->,VAL_2201_STATUS,,__BOOL_LITERAL(FALSE));
      } else {
        __SET_EXTERNAL(data__->,VAL_2201_STATUS,,__BOOL_LITERAL(FALSE));
      };
    } else {
      __SET_EXTERNAL(data__->,VAL_2201_STATUS,,__BOOL_LITERAL(FALSE));
    };
  } else {
    __SET_EXTERNAL(data__->,VAL_2201_STATUS,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // FB_EQ_VAL_2201_body__() 





void CLX_0005_init__(CLX_0005_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,AIT_2301,data__->AIT_2301,retain)
  __INIT_EXTERNAL(REAL,AIT_2301_HH_SP,data__->AIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_CMD,data__->FCV_2301_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0005_body__(CLX_0005_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->AIT_2301,) >= __GET_EXTERNAL(data__->AIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,FCV_2301_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0005_body__() 





void CLX_0007_init__(CLX_0007_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,AIT_2301,data__->AIT_2301,retain)
  __INIT_EXTERNAL(REAL,AIT_2301_HH_SP,data__->AIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_CMD,data__->VAL_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0007_body__(CLX_0007_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->AIT_2301,) >= __GET_EXTERNAL(data__->AIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,VAL_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0007_body__() 





void CLX_0009_init__(CLX_0009_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,DPIT_2101,data__->DPIT_2101,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101_HH_SP,data__->DPIT_2101_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_CMD,data__->FCV_2301_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0009_body__(CLX_0009_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->DPIT_2101,) >= __GET_EXTERNAL(data__->DPIT_2101_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,FCV_2301_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0009_body__() 





void CLX_0011_init__(CLX_0011_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,DPIT_2101,data__->DPIT_2101,retain)
  __INIT_EXTERNAL(REAL,DPIT_2101_HH_SP,data__->DPIT_2101_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_CMD,data__->VAL_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0011_body__(CLX_0011_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->DPIT_2101,) >= __GET_EXTERNAL(data__->DPIT_2101_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,VAL_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0011_body__() 





void CLX_0027_init__(CLX_0027_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0027_body__(CLX_0027_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,P_20_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0027_body__() 





void CLX_0013_init__(CLX_0013_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0013_body__(CLX_0013_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2001_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0013_body__() 





void CLX_0015_init__(CLX_0015_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0015_body__(CLX_0015_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2002_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0015_body__() 





void CLX_0017_init__(CLX_0017_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0017_body__(CLX_0017_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0017_body__() 





void CLX_0019_init__(CLX_0019_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0019_body__(CLX_0019_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2601_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0019_body__() 





void CLX_0021_init__(CLX_0021_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0021_body__(CLX_0021_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2602_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0021_body__() 





void CLX_0023_init__(CLX_0023_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0023_body__(CLX_0023_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4501_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0023_body__() 





void CLX_0025_init__(CLX_0025_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_2301,data__->FIT_2301,retain)
  __INIT_EXTERNAL(REAL,FIT_2301_HH_SP,data__->FIT_2301_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0025_body__(CLX_0025_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_2301,) >= __GET_EXTERNAL(data__->FIT_2301_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4502_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0025_body__() 





void CLX_0043_init__(CLX_0043_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0043_body__(CLX_0043_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,P_20_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0043_body__() 





void CLX_0029_init__(CLX_0029_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0029_body__(CLX_0029_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2001_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0029_body__() 





void CLX_0031_init__(CLX_0031_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0031_body__(CLX_0031_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2002_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0031_body__() 





void CLX_0033_init__(CLX_0033_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0033_body__(CLX_0033_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0033_body__() 





void CLX_0035_init__(CLX_0035_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0035_body__(CLX_0035_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2601_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0035_body__() 





void CLX_0037_init__(CLX_0037_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0037_body__(CLX_0037_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2602_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0037_body__() 





void CLX_0039_init__(CLX_0039_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0039_body__(CLX_0039_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4501_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0039_body__() 





void CLX_0041_init__(CLX_0041_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,FIT_4501,data__->FIT_4501,retain)
  __INIT_EXTERNAL(REAL,FIT_4501_HH_SP,data__->FIT_4501_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0041_body__(CLX_0041_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->FIT_4501,) >= __GET_EXTERNAL(data__->FIT_4501_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4502_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0041_body__() 





void CLX_0059_init__(CLX_0059_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0059_body__(CLX_0059_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,P_20_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0059_body__() 





void CLX_0045_init__(CLX_0045_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0045_body__(CLX_0045_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2001_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0045_body__() 





void CLX_0047_init__(CLX_0047_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0047_body__(CLX_0047_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2002_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0047_body__() 





void CLX_0049_init__(CLX_0049_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0049_body__(CLX_0049_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0049_body__() 





void CLX_0051_init__(CLX_0051_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0051_body__(CLX_0051_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2601_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0051_body__() 





void CLX_0053_init__(CLX_0053_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0053_body__(CLX_0053_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2602_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0053_body__() 





void CLX_0055_init__(CLX_0055_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0055_body__(CLX_0055_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4501_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0055_body__() 





void CLX_0057_init__(CLX_0057_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2001,data__->LIT_2001,retain)
  __INIT_EXTERNAL(REAL,LIT_2001_HH_SP,data__->LIT_2001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0057_body__(CLX_0057_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2001,) >= __GET_EXTERNAL(data__->LIT_2001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4502_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0057_body__() 





void CLX_0075_init__(CLX_0075_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0075_body__(CLX_0075_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,P_20_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0075_body__() 





void CLX_0061_init__(CLX_0061_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0061_body__(CLX_0061_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2001_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0061_body__() 





void CLX_0063_init__(CLX_0063_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0063_body__(CLX_0063_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2002_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0063_body__() 





void CLX_0065_init__(CLX_0065_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0065_body__(CLX_0065_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0065_body__() 





void CLX_0067_init__(CLX_0067_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0067_body__(CLX_0067_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2601_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0067_body__() 





void CLX_0069_init__(CLX_0069_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0069_body__(CLX_0069_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2602_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0069_body__() 





void CLX_0071_init__(CLX_0071_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0071_body__(CLX_0071_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4501_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0071_body__() 





void CLX_0073_init__(CLX_0073_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,LIT_2601,data__->LIT_2601,retain)
  __INIT_EXTERNAL(REAL,LIT_2601_HH_SP,data__->LIT_2601_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0073_body__(CLX_0073_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LIT_2601,) >= __GET_EXTERNAL(data__->LIT_2601_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4502_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0073_body__() 





void CLX_0091_init__(CLX_0091_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0091_body__(CLX_0091_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSHH_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,P_20_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0091_body__() 





void CLX_0077_init__(CLX_0077_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0077_body__(CLX_0077_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSHH_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2001_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0077_body__() 





void CLX_0079_init__(CLX_0079_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0079_body__(CLX_0079_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSHH_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2002_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0079_body__() 





void CLX_0081_init__(CLX_0081_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0081_body__(CLX_0081_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSHH_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0081_body__() 





void CLX_0083_init__(CLX_0083_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0083_body__(CLX_0083_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSHH_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2601_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0083_body__() 





void CLX_0085_init__(CLX_0085_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0085_body__(CLX_0085_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSHH_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2602_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0085_body__() 





void CLX_0087_init__(CLX_0087_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0087_body__(CLX_0087_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSHH_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4501_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0087_body__() 





void CLX_0089_init__(CLX_0089_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSHH_2001,data__->LSHH_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0089_body__(CLX_0089_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSHH_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4502_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0089_body__() 





void CLX_0107_init__(CLX_0107_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0107_body__(CLX_0107_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSLL_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,P_20_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0107_body__() 





void CLX_0093_init__(CLX_0093_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0093_body__(CLX_0093_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSLL_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2001_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0093_body__() 





void CLX_0095_init__(CLX_0095_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0095_body__(CLX_0095_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSLL_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2002_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0095_body__() 





void CLX_0097_init__(CLX_0097_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0097_body__(CLX_0097_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSLL_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0097_body__() 





void CLX_0099_init__(CLX_0099_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0099_body__(CLX_0099_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSLL_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2601_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0099_body__() 





void CLX_0101_init__(CLX_0101_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0101_body__(CLX_0101_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSLL_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_2602_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0101_body__() 





void CLX_0103_init__(CLX_0103_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0103_body__(CLX_0103_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSLL_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4501_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0103_body__() 





void CLX_0105_init__(CLX_0105_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,LSLL_2001,data__->LSLL_2001,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0105_body__(CLX_0105_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->LSLL_2001,) == __BOOL_LITERAL(TRUE)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,PMP_4502_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0105_body__() 





void CLX_0109_init__(CLX_0109_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_CMD,data__->FCV_2301_CMD,retain)
  __INIT_EXTERNAL(REAL,PIT_4001,data__->PIT_4001,retain)
  __INIT_EXTERNAL(REAL,PIT_4001_HH_SP,data__->PIT_4001_HH_SP,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0109_body__(CLX_0109_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->PIT_4001,) >= __GET_EXTERNAL(data__->PIT_4001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,FCV_2301_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0109_body__() 





void CLX_0111_init__(CLX_0111_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(REAL,PIT_4001,data__->PIT_4001,retain)
  __INIT_EXTERNAL(REAL,PIT_4001_HH_SP,data__->PIT_4001_HH_SP,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_CMD,data__->VAL_2201_CMD,retain)
  __INIT_VAR(data__->INTERLOCK_ACTIVE,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void CLX_0111_body__(CLX_0111_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,INTERLOCK_ACTIVE,,(__GET_EXTERNAL(data__->PIT_4001,) >= __GET_EXTERNAL(data__->PIT_4001_HH_SP,)));
  if (__GET_VAR(data__->INTERLOCK_ACTIVE,)) {
    __SET_EXTERNAL(data__->,VAL_2201_CMD,,__BOOL_LITERAL(FALSE));
  };

  goto __end;

__end:
  return;
} // CLX_0111_body__() 





void CLX_0223_init__(CLX_0223_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,PLANT_FAULT_ACTIVE,data__->PLANT_FAULT_ACTIVE,retain)
  __INIT_EXTERNAL(BOOL,ALM_BL_4001_FAULT,data__->ALM_BL_4001_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_BL_4002_FAULT,data__->ALM_BL_4002_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_FCV_2301_FAULT,data__->ALM_FCV_2301_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2001_FAULT,data__->ALM_PMP_2001_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2002_FAULT,data__->ALM_PMP_2002_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2201_FAULT,data__->ALM_PMP_2201_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2601_FAULT,data__->ALM_PMP_2601_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_2602_FAULT,data__->ALM_PMP_2602_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_4501_FAULT,data__->ALM_PMP_4501_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_PMP_4502_FAULT,data__->ALM_PMP_4502_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_P_20_FAULT,data__->ALM_P_20_FAULT,retain)
  __INIT_EXTERNAL(BOOL,ALM_VAL_2201_FAULT,data__->ALM_VAL_2201_FAULT,retain)
}

// Code part
void CLX_0223_body__(CLX_0223_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(FALSE));
  if (__GET_EXTERNAL(data__->ALM_BL_4001_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_BL_4002_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_FCV_2301_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_PMP_2001_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_PMP_2002_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_PMP_2201_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_PMP_2601_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_PMP_2602_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_PMP_4501_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_PMP_4502_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_P_20_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };
  if (__GET_EXTERNAL(data__->ALM_VAL_2201_FAULT,)) {
    __SET_EXTERNAL(data__->,PLANT_FAULT_ACTIVE,,__BOOL_LITERAL(TRUE));
  };

  goto __end;

__end:
  return;
} // CLX_0223_body__() 





void FB_R_TRIG_init__(FB_R_TRIG_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->CLK,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->Q,__BOOL_LITERAL(FALSE),retain)
  __INIT_VAR(data__->MEM,__BOOL_LITERAL(FALSE),retain)
}

// Code part
void FB_R_TRIG_body__(FB_R_TRIG_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->,Q,,(__GET_VAR(data__->CLK,) && !(__GET_VAR(data__->MEM,))));
  __SET_VAR(data__->,MEM,,__GET_VAR(data__->CLK,));

  goto __end;

__end:
  return;
} // FB_R_TRIG_body__() 





void FB_SHUTDOWN_SEQUENCE_init__(FB_SHUTDOWN_SEQUENCE_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,BL_4001_CMD,data__->BL_4001_CMD,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_CMD,data__->BL_4002_CMD,retain)
  __INIT_EXTERNAL(BOOL,CLK,data__->CLK,retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_AUTO,data__->FCV_2301_AUTO,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_CMD,data__->FCV_2301_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_EXTERNAL(BOOL,PROCESS_STOPPED,data__->PROCESS_STOPPED,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_EXTERNAL(BOOL,Q,data__->Q,retain)
  __INIT_EXTERNAL(BOOL,SHUTDOWN_CMD,data__->SHUTDOWN_CMD,retain)
  __INIT_EXTERNAL(BOOL,SHUTDOWN_HOLD_OK,data__->SHUTDOWN_HOLD_OK,retain)
  __INIT_EXTERNAL(BOOL,STOP_CONFIRM,data__->STOP_CONFIRM,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_CLOSE_CMD,data__->VAL_2201_CLOSE_CMD,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_CMD,data__->VAL_2201_CMD,retain)
  __INIT_VAR(data__->STEPSTATE,__INT_LITERAL(0),retain)
  FB_R_TRIG_init__(&data__->STOPEDGE,retain);
}

// Code part
void FB_SHUTDOWN_SEQUENCE_body__(FB_SHUTDOWN_SEQUENCE_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->STOPEDGE.,CLK,,__GET_EXTERNAL(data__->SHUTDOWN_CMD,));
  FB_R_TRIG_body__(&data__->STOPEDGE);
  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) != PLANT_STATE__PLANT_STOPPING)) {
    __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(0));
  } else if (!(__GET_EXTERNAL(data__->SHUTDOWN_CMD,))) {
    __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(0));
  } else {
    {
      INT __case_expression = __GET_VAR(data__->STEPSTATE,);
      if ((__case_expression == __INT_LITERAL(0))) {
        if (__GET_VAR(data__->STOPEDGE.Q,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(10));
        };
      }
      else if ((__case_expression == __INT_LITERAL(10))) {
        __SET_EXTERNAL(data__->,FCV_2301_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->SHUTDOWN_CMD,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(20));
        };
      }
      else if ((__case_expression == __INT_LITERAL(20))) {
        __SET_EXTERNAL(data__->,FCV_2301_AUTO,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->SHUTDOWN_CMD,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(30));
        };
      }
      else if ((__case_expression == __INT_LITERAL(30))) {
        __SET_EXTERNAL(data__->,PMP_4502_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(40));
        };
      }
      else if ((__case_expression == __INT_LITERAL(40))) {
        __SET_EXTERNAL(data__->,PMP_4501_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(50));
        };
      }
      else if ((__case_expression == __INT_LITERAL(50))) {
        __SET_EXTERNAL(data__->,PMP_2602_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(60));
        };
      }
      else if ((__case_expression == __INT_LITERAL(60))) {
        __SET_EXTERNAL(data__->,PMP_2601_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(70));
        };
      }
      else if ((__case_expression == __INT_LITERAL(70))) {
        __SET_EXTERNAL(data__->,PMP_2201_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(80));
        };
      }
      else if ((__case_expression == __INT_LITERAL(80))) {
        __SET_EXTERNAL(data__->,PMP_2002_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(90));
        };
      }
      else if ((__case_expression == __INT_LITERAL(90))) {
        __SET_EXTERNAL(data__->,PMP_2001_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(100));
        };
      }
      else if ((__case_expression == __INT_LITERAL(100))) {
        __SET_EXTERNAL(data__->,P_20_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(110));
        };
      }
      else if ((__case_expression == __INT_LITERAL(110))) {
        __SET_EXTERNAL(data__->,BL_4002_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(120));
        };
      }
      else if ((__case_expression == __INT_LITERAL(120))) {
        __SET_EXTERNAL(data__->,BL_4001_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(130));
        };
      }
      else if ((__case_expression == __INT_LITERAL(130))) {
        __SET_EXTERNAL(data__->,VAL_2201_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(140));
        };
      }
      else if ((__case_expression == __INT_LITERAL(140))) {
        __SET_EXTERNAL(data__->,VAL_2201_CLOSE_CMD,,__BOOL_LITERAL(FALSE));
        if (__GET_EXTERNAL(data__->STOP_CONFIRM,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(150));
        };
      }
      else if ((__case_expression == __INT_LITERAL(150))) {
        __SET_EXTERNAL(data__->,PROCESS_STOPPED,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->SHUTDOWN_HOLD_OK,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(0));
        };
      }
      else {
        __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(0));
      }
    };
  };

  goto __end;

__end:
  return;
} // FB_SHUTDOWN_SEQUENCE_body__() 





void FB_STARTUP_SEQUENCE_init__(FB_STARTUP_SEQUENCE_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(BOOL,BL_4001_CMD,data__->BL_4001_CMD,retain)
  __INIT_EXTERNAL(BOOL,BL_4001_STATUS,data__->BL_4001_STATUS,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_CMD,data__->BL_4002_CMD,retain)
  __INIT_EXTERNAL(BOOL,BL_4002_STATUS,data__->BL_4002_STATUS,retain)
  __INIT_EXTERNAL(BOOL,CLK,data__->CLK,retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_AUTO,data__->FCV_2301_AUTO,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_CMD,data__->FCV_2301_CMD,retain)
  __INIT_EXTERNAL(BOOL,FCV_2301_STATUS,data__->FCV_2301_STATUS,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_CMD,data__->PMP_2001_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2001_STATUS,data__->PMP_2001_STATUS,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_CMD,data__->PMP_2002_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2002_STATUS,data__->PMP_2002_STATUS,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_CMD,data__->PMP_2201_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2201_STATUS,data__->PMP_2201_STATUS,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_CMD,data__->PMP_2601_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2601_STATUS,data__->PMP_2601_STATUS,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_CMD,data__->PMP_2602_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_2602_STATUS,data__->PMP_2602_STATUS,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_CMD,data__->PMP_4501_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_4501_STATUS,data__->PMP_4501_STATUS,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_CMD,data__->PMP_4502_CMD,retain)
  __INIT_EXTERNAL(BOOL,PMP_4502_STATUS,data__->PMP_4502_STATUS,retain)
  __INIT_EXTERNAL(BOOL,PROCESS_RUNNING,data__->PROCESS_RUNNING,retain)
  __INIT_EXTERNAL(BOOL,P_20_CMD,data__->P_20_CMD,retain)
  __INIT_EXTERNAL(BOOL,P_20_STATUS,data__->P_20_STATUS,retain)
  __INIT_EXTERNAL(BOOL,Q,data__->Q,retain)
  __INIT_EXTERNAL(BOOL,STARTUP_CMD,data__->STARTUP_CMD,retain)
  __INIT_EXTERNAL(BOOL,STARTUP_HOLD_OK,data__->STARTUP_HOLD_OK,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_CMD,data__->VAL_2201_CMD,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_OPEN_CMD,data__->VAL_2201_OPEN_CMD,retain)
  __INIT_EXTERNAL(BOOL,VAL_2201_STATUS,data__->VAL_2201_STATUS,retain)
  __INIT_VAR(data__->STEPSTATE,__INT_LITERAL(0),retain)
  FB_R_TRIG_init__(&data__->STARTEDGE,retain);
}

// Code part
void FB_STARTUP_SEQUENCE_body__(FB_STARTUP_SEQUENCE_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->STARTEDGE.,CLK,,__GET_EXTERNAL(data__->STARTUP_CMD,));
  FB_R_TRIG_body__(&data__->STARTEDGE);
  if ((__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,) != PLANT_STATE__PLANT_STARTING)) {
    __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(0));
  } else if (!(__GET_EXTERNAL(data__->STARTUP_CMD,))) {
    __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(0));
  } else {
    {
      INT __case_expression = __GET_VAR(data__->STEPSTATE,);
      if ((__case_expression == __INT_LITERAL(0))) {
        if (__GET_VAR(data__->STARTEDGE.Q,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(10));
        };
      }
      else if ((__case_expression == __INT_LITERAL(10))) {
        __SET_EXTERNAL(data__->,VAL_2201_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->VAL_2201_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(20));
        };
      }
      else if ((__case_expression == __INT_LITERAL(20))) {
        __SET_EXTERNAL(data__->,VAL_2201_OPEN_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->VAL_2201_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(30));
        };
      }
      else if ((__case_expression == __INT_LITERAL(30))) {
        __SET_EXTERNAL(data__->,BL_4001_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->BL_4001_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(40));
        };
      }
      else if ((__case_expression == __INT_LITERAL(40))) {
        __SET_EXTERNAL(data__->,BL_4002_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->BL_4002_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(50));
        };
      }
      else if ((__case_expression == __INT_LITERAL(50))) {
        __SET_EXTERNAL(data__->,P_20_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->P_20_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(60));
        };
      }
      else if ((__case_expression == __INT_LITERAL(60))) {
        __SET_EXTERNAL(data__->,PMP_2001_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->PMP_2001_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(70));
        };
      }
      else if ((__case_expression == __INT_LITERAL(70))) {
        __SET_EXTERNAL(data__->,PMP_2002_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->PMP_2002_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(80));
        };
      }
      else if ((__case_expression == __INT_LITERAL(80))) {
        __SET_EXTERNAL(data__->,PMP_2201_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->PMP_2201_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(90));
        };
      }
      else if ((__case_expression == __INT_LITERAL(90))) {
        __SET_EXTERNAL(data__->,PMP_2601_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->PMP_2601_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(100));
        };
      }
      else if ((__case_expression == __INT_LITERAL(100))) {
        __SET_EXTERNAL(data__->,PMP_2602_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->PMP_2602_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(110));
        };
      }
      else if ((__case_expression == __INT_LITERAL(110))) {
        __SET_EXTERNAL(data__->,PMP_4501_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->PMP_4501_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(120));
        };
      }
      else if ((__case_expression == __INT_LITERAL(120))) {
        __SET_EXTERNAL(data__->,PMP_4502_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->PMP_4502_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(130));
        };
      }
      else if ((__case_expression == __INT_LITERAL(130))) {
        __SET_EXTERNAL(data__->,FCV_2301_CMD,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->FCV_2301_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(140));
        };
      }
      else if ((__case_expression == __INT_LITERAL(140))) {
        __SET_EXTERNAL(data__->,FCV_2301_AUTO,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->FCV_2301_STATUS,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(150));
        };
      }
      else if ((__case_expression == __INT_LITERAL(150))) {
        __SET_EXTERNAL(data__->,PROCESS_RUNNING,,__BOOL_LITERAL(TRUE));
        if (__GET_EXTERNAL(data__->STARTUP_HOLD_OK,)) {
          __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(0));
        };
      }
      else {
        __SET_VAR(data__->,STEPSTATE,,__INT_LITERAL(0));
      }
    };
  };

  goto __end;

__end:
  return;
} // FB_STARTUP_SEQUENCE_body__() 





void CLX_0225_init__(CLX_0225_data__ *data__, BOOL retain) {
  __INIT_VAR(data__->EN,__BOOL_LITERAL(TRUE),retain)
  __INIT_VAR(data__->ENO,__BOOL_LITERAL(TRUE),retain)
  __INIT_EXTERNAL(PLANT_STATE,CURRENT_PLANT_STATE,data__->CURRENT_PLANT_STATE,retain)
  __INIT_EXTERNAL(PLANT_STATE,NEXT_PLANT_STATE,data__->NEXT_PLANT_STATE,retain)
  __INIT_EXTERNAL(BOOL,PLANT_START_CMD,data__->PLANT_START_CMD,retain)
  __INIT_EXTERNAL(BOOL,PLANT_STOP_CMD,data__->PLANT_STOP_CMD,retain)
  __INIT_EXTERNAL(BOOL,PLANT_FAULT_ACTIVE,data__->PLANT_FAULT_ACTIVE,retain)
  __INIT_EXTERNAL(BOOL,PROCESS_RUNNING,data__->PROCESS_RUNNING,retain)
  __INIT_EXTERNAL(BOOL,PROCESS_STOPPED,data__->PROCESS_STOPPED,retain)
  __INIT_EXTERNAL(BOOL,CLK,data__->CLK,retain)
  __INIT_EXTERNAL(BOOL,Q,data__->Q,retain)
  FB_R_TRIG_init__(&data__->STARTEDGE,retain);
  FB_R_TRIG_init__(&data__->STOPEDGE,retain);
}

// Code part
void CLX_0225_body__(CLX_0225_data__ *data__) {
  // Control execution
  if (!__GET_VAR(data__->EN)) {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(FALSE));
    return;
  }
  else {
    __SET_VAR(data__->,ENO,,__BOOL_LITERAL(TRUE));
  }
  // Initialise TEMP variables

  __SET_VAR(data__->STARTEDGE.,CLK,,__GET_EXTERNAL(data__->PLANT_START_CMD,));
  FB_R_TRIG_body__(&data__->STARTEDGE);
  __SET_VAR(data__->STOPEDGE.,CLK,,__GET_EXTERNAL(data__->PLANT_STOP_CMD,));
  FB_R_TRIG_body__(&data__->STOPEDGE);
  __SET_EXTERNAL(data__->,NEXT_PLANT_STATE,,__GET_EXTERNAL(data__->CURRENT_PLANT_STATE,));
  {
    PLANT_STATE __case_expression = __GET_EXTERNAL(data__->CURRENT_PLANT_STATE,);
    if ((__case_expression == PLANT_STATE__PLANT_STOPPED)) {
      if (__GET_VAR(data__->STARTEDGE.Q,)) {
        __SET_EXTERNAL(data__->,NEXT_PLANT_STATE,,PLANT_STATE__PLANT_STARTING);
      };
    }
    else if ((__case_expression == PLANT_STATE__PLANT_STARTING)) {
      if (__GET_EXTERNAL(data__->PROCESS_RUNNING,)) {
        __SET_EXTERNAL(data__->,NEXT_PLANT_STATE,,PLANT_STATE__PLANT_RUNNING);
      };
      if (__GET_EXTERNAL(data__->PLANT_FAULT_ACTIVE,)) {
        __SET_EXTERNAL(data__->,NEXT_PLANT_STATE,,PLANT_STATE__PLANT_FAULT);
      };
    }
    else if ((__case_expression == PLANT_STATE__PLANT_RUNNING)) {
      if (__GET_VAR(data__->STOPEDGE.Q,)) {
        __SET_EXTERNAL(data__->,NEXT_PLANT_STATE,,PLANT_STATE__PLANT_STOPPING);
      };
      if (__GET_EXTERNAL(data__->PLANT_FAULT_ACTIVE,)) {
        __SET_EXTERNAL(data__->,NEXT_PLANT_STATE,,PLANT_STATE__PLANT_FAULT);
      };
    }
    else if ((__case_expression == PLANT_STATE__PLANT_STOPPING)) {
      if (__GET_EXTERNAL(data__->PROCESS_STOPPED,)) {
        __SET_EXTERNAL(data__->,NEXT_PLANT_STATE,,PLANT_STATE__PLANT_STOPPED);
      };
    }
    else if ((__case_expression == PLANT_STATE__PLANT_FAULT)) {
      if (!(__GET_EXTERNAL(data__->PLANT_FAULT_ACTIVE,))) {
        __SET_EXTERNAL(data__->,NEXT_PLANT_STATE,,PLANT_STATE__PLANT_STOPPED);
      };
    }
  };
  __SET_EXTERNAL(data__->,CURRENT_PLANT_STATE,,__GET_EXTERNAL(data__->NEXT_PLANT_STATE,));

  goto __end;

__end:
  return;
} // CLX_0225_body__() 





void CLX_0001_init__(CLX_0001_data__ *data__, BOOL retain) {
  CLX_0003_init__(&data__->CLX_0002,retain);
  FB_EQ_BL_4001_init__(&data__->INST_EQ_BL_4001,retain);
  FB_EQ_BL_4002_init__(&data__->INST_EQ_BL_4002,retain);
  FB_EQ_FCV_2301_init__(&data__->INST_EQ_FCV_2301,retain);
  FB_EQ_PMP_2001_init__(&data__->INST_EQ_PMP_2001,retain);
  FB_EQ_PMP_2002_init__(&data__->INST_EQ_PMP_2002,retain);
  FB_EQ_PMP_2201_init__(&data__->INST_EQ_PMP_2201,retain);
  FB_EQ_PMP_2601_init__(&data__->INST_EQ_PMP_2601,retain);
  FB_EQ_PMP_2602_init__(&data__->INST_EQ_PMP_2602,retain);
  FB_EQ_PMP_4501_init__(&data__->INST_EQ_PMP_4501,retain);
  FB_EQ_PMP_4502_init__(&data__->INST_EQ_PMP_4502,retain);
  FB_EQ_P_20_init__(&data__->INST_EQ_P_20,retain);
  FB_EQ_VAL_2201_init__(&data__->INST_EQ_VAL_2201,retain);
  CLX_0005_init__(&data__->CLX_0004,retain);
  CLX_0007_init__(&data__->CLX_0006,retain);
  CLX_0009_init__(&data__->CLX_0008,retain);
  CLX_0011_init__(&data__->CLX_0010,retain);
  CLX_0013_init__(&data__->CLX_0012,retain);
  CLX_0015_init__(&data__->CLX_0014,retain);
  CLX_0017_init__(&data__->CLX_0016,retain);
  CLX_0019_init__(&data__->CLX_0018,retain);
  CLX_0021_init__(&data__->CLX_0020,retain);
  CLX_0023_init__(&data__->CLX_0022,retain);
  CLX_0025_init__(&data__->CLX_0024,retain);
  CLX_0027_init__(&data__->CLX_0026,retain);
  CLX_0029_init__(&data__->CLX_0028,retain);
  CLX_0031_init__(&data__->CLX_0030,retain);
  CLX_0033_init__(&data__->CLX_0032,retain);
  CLX_0035_init__(&data__->CLX_0034,retain);
  CLX_0037_init__(&data__->CLX_0036,retain);
  CLX_0039_init__(&data__->CLX_0038,retain);
  CLX_0041_init__(&data__->CLX_0040,retain);
  CLX_0043_init__(&data__->CLX_0042,retain);
  CLX_0045_init__(&data__->CLX_0044,retain);
  CLX_0047_init__(&data__->CLX_0046,retain);
  CLX_0049_init__(&data__->CLX_0048,retain);
  CLX_0051_init__(&data__->CLX_0050,retain);
  CLX_0053_init__(&data__->CLX_0052,retain);
  CLX_0055_init__(&data__->CLX_0054,retain);
  CLX_0057_init__(&data__->CLX_0056,retain);
  CLX_0059_init__(&data__->CLX_0058,retain);
  CLX_0061_init__(&data__->CLX_0060,retain);
  CLX_0063_init__(&data__->CLX_0062,retain);
  CLX_0065_init__(&data__->CLX_0064,retain);
  CLX_0067_init__(&data__->CLX_0066,retain);
  CLX_0069_init__(&data__->CLX_0068,retain);
  CLX_0071_init__(&data__->CLX_0070,retain);
  CLX_0073_init__(&data__->CLX_0072,retain);
  CLX_0075_init__(&data__->CLX_0074,retain);
  CLX_0077_init__(&data__->CLX_0076,retain);
  CLX_0079_init__(&data__->CLX_0078,retain);
  CLX_0081_init__(&data__->CLX_0080,retain);
  CLX_0083_init__(&data__->CLX_0082,retain);
  CLX_0085_init__(&data__->CLX_0084,retain);
  CLX_0087_init__(&data__->CLX_0086,retain);
  CLX_0089_init__(&data__->CLX_0088,retain);
  CLX_0091_init__(&data__->CLX_0090,retain);
  CLX_0093_init__(&data__->CLX_0092,retain);
  CLX_0095_init__(&data__->CLX_0094,retain);
  CLX_0097_init__(&data__->CLX_0096,retain);
  CLX_0099_init__(&data__->CLX_0098,retain);
  CLX_0101_init__(&data__->CLX_0100,retain);
  CLX_0103_init__(&data__->CLX_0102,retain);
  CLX_0105_init__(&data__->CLX_0104,retain);
  CLX_0107_init__(&data__->CLX_0106,retain);
  CLX_0109_init__(&data__->CLX_0108,retain);
  CLX_0111_init__(&data__->CLX_0110,retain);
  CLX_0113_init__(&data__->CLX_0112,retain);
  CLX_0115_init__(&data__->CLX_0114,retain);
  CLX_0117_init__(&data__->CLX_0116,retain);
  CLX_0119_init__(&data__->CLX_0118,retain);
  CLX_0121_init__(&data__->CLX_0120,retain);
  CLX_0123_init__(&data__->CLX_0122,retain);
  CLX_0125_init__(&data__->CLX_0124,retain);
  CLX_0127_init__(&data__->CLX_0126,retain);
  CLX_0129_init__(&data__->CLX_0128,retain);
  CLX_0131_init__(&data__->CLX_0130,retain);
  CLX_0133_init__(&data__->CLX_0132,retain);
  CLX_0135_init__(&data__->CLX_0134,retain);
  CLX_0137_init__(&data__->CLX_0136,retain);
  CLX_0139_init__(&data__->CLX_0138,retain);
  CLX_0141_init__(&data__->CLX_0140,retain);
  CLX_0143_init__(&data__->CLX_0142,retain);
  CLX_0145_init__(&data__->CLX_0144,retain);
  CLX_0147_init__(&data__->CLX_0146,retain);
  CLX_0149_init__(&data__->CLX_0148,retain);
  CLX_0151_init__(&data__->CLX_0150,retain);
  CLX_0153_init__(&data__->CLX_0152,retain);
  CLX_0155_init__(&data__->CLX_0154,retain);
  CLX_0157_init__(&data__->CLX_0156,retain);
  CLX_0159_init__(&data__->CLX_0158,retain);
  CLX_0161_init__(&data__->CLX_0160,retain);
  CLX_0163_init__(&data__->CLX_0162,retain);
  CLX_0165_init__(&data__->CLX_0164,retain);
  CLX_0167_init__(&data__->CLX_0166,retain);
  CLX_0169_init__(&data__->CLX_0168,retain);
  CLX_0171_init__(&data__->CLX_0170,retain);
  CLX_0173_init__(&data__->CLX_0172,retain);
  CLX_0175_init__(&data__->CLX_0174,retain);
  CLX_0177_init__(&data__->CLX_0176,retain);
  CLX_0179_init__(&data__->CLX_0178,retain);
  CLX_0181_init__(&data__->CLX_0180,retain);
  CLX_0183_init__(&data__->CLX_0182,retain);
  CLX_0185_init__(&data__->CLX_0184,retain);
  CLX_0187_init__(&data__->CLX_0186,retain);
  CLX_0189_init__(&data__->CLX_0188,retain);
  CLX_0191_init__(&data__->CLX_0190,retain);
  CLX_0193_init__(&data__->CLX_0192,retain);
  CLX_0195_init__(&data__->CLX_0194,retain);
  CLX_0197_init__(&data__->CLX_0196,retain);
  CLX_0199_init__(&data__->CLX_0198,retain);
  CLX_0201_init__(&data__->CLX_0200,retain);
  CLX_0203_init__(&data__->CLX_0202,retain);
  CLX_0205_init__(&data__->CLX_0204,retain);
  CLX_0207_init__(&data__->CLX_0206,retain);
  CLX_0209_init__(&data__->CLX_0208,retain);
  CLX_0211_init__(&data__->CLX_0210,retain);
  CLX_0213_init__(&data__->CLX_0212,retain);
  CLX_0215_init__(&data__->CLX_0214,retain);
  CLX_0217_init__(&data__->CLX_0216,retain);
  CLX_0219_init__(&data__->CLX_0218,retain);
  FB_SHUTDOWN_SEQUENCE_init__(&data__->CLX_0220,retain);
  FB_STARTUP_SEQUENCE_init__(&data__->CLX_0221,retain);
  CLX_0223_init__(&data__->CLX_0222,retain);
  CLX_0225_init__(&data__->CLX_0224,retain);
  __INIT_VAR(data__->CLX_DUMMY,__BOOL_LITERAL(FALSE),retain)
  __INIT_EXTERNAL(BOOL,STARTUP_CMD,data__->STARTUP_CMD,retain)
  __INIT_EXTERNAL(BOOL,SHUTDOWN_CMD,data__->SHUTDOWN_CMD,retain)
  __INIT_EXTERNAL(BOOL,PLANT_START_CMD,data__->PLANT_START_CMD,retain)
  __INIT_EXTERNAL(BOOL,PLANT_STOP_CMD,data__->PLANT_STOP_CMD,retain)
  __INIT_EXTERNAL(BOOL,ALARMS,data__->ALARMS,retain)
  __INIT_EXTERNAL(BOOL,EQUIPMENT,data__->EQUIPMENT,retain)
  __INIT_EXTERNAL(BOOL,CLX_0226,data__->CLX_0226,retain)
  __INIT_EXTERNAL(BOOL,CLX_0227,data__->CLX_0227,retain)
  __INIT_EXTERNAL(BOOL,INTERLOCKS,data__->INTERLOCKS,retain)
  __INIT_EXTERNAL(BOOL,CLX_0228,data__->CLX_0228,retain)
  __INIT_EXTERNAL(BOOL,LOOPS,data__->LOOPS,retain)
  __INIT_EXTERNAL(BOOL,CLX_0229,data__->CLX_0229,retain)
  __INIT_EXTERNAL(BOOL,CLX_0230,data__->CLX_0230,retain)
  __INIT_EXTERNAL(BOOL,SEQUENCES,data__->SEQUENCES,retain)
  __INIT_EXTERNAL(BOOL,SUPERVISORS,data__->SUPERVISORS,retain)
  __INIT_EXTERNAL(BOOL,SYSTEM,data__->SYSTEM,retain)
  __INIT_EXTERNAL(BOOL,CLX_0231,data__->CLX_0231,retain)
}

// Code part
void CLX_0001_body__(CLX_0001_data__ *data__) {
  // Initialise TEMP variables

  __SET_EXTERNAL(data__->,PLANT_START_CMD,,__GET_EXTERNAL(data__->STARTUP_CMD,));
  __SET_EXTERNAL(data__->,PLANT_STOP_CMD,,__GET_EXTERNAL(data__->SHUTDOWN_CMD,));
  CLX_0223_body__(&data__->CLX_0222);
  CLX_0225_body__(&data__->CLX_0224);
  CLX_0005_body__(&data__->CLX_0004);
  CLX_0007_body__(&data__->CLX_0006);
  CLX_0009_body__(&data__->CLX_0008);
  CLX_0011_body__(&data__->CLX_0010);
  CLX_0027_body__(&data__->CLX_0026);
  CLX_0013_body__(&data__->CLX_0012);
  CLX_0015_body__(&data__->CLX_0014);
  CLX_0017_body__(&data__->CLX_0016);
  CLX_0019_body__(&data__->CLX_0018);
  CLX_0021_body__(&data__->CLX_0020);
  CLX_0023_body__(&data__->CLX_0022);
  CLX_0025_body__(&data__->CLX_0024);
  CLX_0043_body__(&data__->CLX_0042);
  CLX_0029_body__(&data__->CLX_0028);
  CLX_0031_body__(&data__->CLX_0030);
  CLX_0033_body__(&data__->CLX_0032);
  CLX_0035_body__(&data__->CLX_0034);
  CLX_0037_body__(&data__->CLX_0036);
  CLX_0039_body__(&data__->CLX_0038);
  CLX_0041_body__(&data__->CLX_0040);
  CLX_0059_body__(&data__->CLX_0058);
  CLX_0045_body__(&data__->CLX_0044);
  CLX_0047_body__(&data__->CLX_0046);
  CLX_0049_body__(&data__->CLX_0048);
  CLX_0051_body__(&data__->CLX_0050);
  CLX_0053_body__(&data__->CLX_0052);
  CLX_0055_body__(&data__->CLX_0054);
  CLX_0057_body__(&data__->CLX_0056);
  CLX_0075_body__(&data__->CLX_0074);
  CLX_0061_body__(&data__->CLX_0060);
  CLX_0063_body__(&data__->CLX_0062);
  CLX_0065_body__(&data__->CLX_0064);
  CLX_0067_body__(&data__->CLX_0066);
  CLX_0069_body__(&data__->CLX_0068);
  CLX_0071_body__(&data__->CLX_0070);
  CLX_0073_body__(&data__->CLX_0072);
  CLX_0091_body__(&data__->CLX_0090);
  CLX_0077_body__(&data__->CLX_0076);
  CLX_0079_body__(&data__->CLX_0078);
  CLX_0081_body__(&data__->CLX_0080);
  CLX_0083_body__(&data__->CLX_0082);
  CLX_0085_body__(&data__->CLX_0084);
  CLX_0087_body__(&data__->CLX_0086);
  CLX_0089_body__(&data__->CLX_0088);
  CLX_0107_body__(&data__->CLX_0106);
  CLX_0093_body__(&data__->CLX_0092);
  CLX_0095_body__(&data__->CLX_0094);
  CLX_0097_body__(&data__->CLX_0096);
  CLX_0099_body__(&data__->CLX_0098);
  CLX_0101_body__(&data__->CLX_0100);
  CLX_0103_body__(&data__->CLX_0102);
  CLX_0105_body__(&data__->CLX_0104);
  CLX_0109_body__(&data__->CLX_0108);
  CLX_0111_body__(&data__->CLX_0110);
  FB_STARTUP_SEQUENCE_body__(&data__->CLX_0221);
  FB_SHUTDOWN_SEQUENCE_body__(&data__->CLX_0220);
  FB_EQ_BL_4001_body__(&data__->INST_EQ_BL_4001);
  FB_EQ_BL_4002_body__(&data__->INST_EQ_BL_4002);
  FB_EQ_FCV_2301_body__(&data__->INST_EQ_FCV_2301);
  FB_EQ_P_20_body__(&data__->INST_EQ_P_20);
  FB_EQ_PMP_2001_body__(&data__->INST_EQ_PMP_2001);
  FB_EQ_PMP_2002_body__(&data__->INST_EQ_PMP_2002);
  FB_EQ_PMP_2201_body__(&data__->INST_EQ_PMP_2201);
  FB_EQ_PMP_2601_body__(&data__->INST_EQ_PMP_2601);
  FB_EQ_PMP_2602_body__(&data__->INST_EQ_PMP_2602);
  FB_EQ_PMP_4501_body__(&data__->INST_EQ_PMP_4501);
  FB_EQ_PMP_4502_body__(&data__->INST_EQ_PMP_4502);
  FB_EQ_VAL_2201_body__(&data__->INST_EQ_VAL_2201);
  CLX_0113_body__(&data__->CLX_0112);
  CLX_0115_body__(&data__->CLX_0114);
  CLX_0117_body__(&data__->CLX_0116);
  CLX_0119_body__(&data__->CLX_0118);
  CLX_0135_body__(&data__->CLX_0134);
  CLX_0121_body__(&data__->CLX_0120);
  CLX_0123_body__(&data__->CLX_0122);
  CLX_0125_body__(&data__->CLX_0124);
  CLX_0127_body__(&data__->CLX_0126);
  CLX_0129_body__(&data__->CLX_0128);
  CLX_0131_body__(&data__->CLX_0130);
  CLX_0133_body__(&data__->CLX_0132);
  CLX_0151_body__(&data__->CLX_0150);
  CLX_0137_body__(&data__->CLX_0136);
  CLX_0139_body__(&data__->CLX_0138);
  CLX_0141_body__(&data__->CLX_0140);
  CLX_0143_body__(&data__->CLX_0142);
  CLX_0145_body__(&data__->CLX_0144);
  CLX_0147_body__(&data__->CLX_0146);
  CLX_0149_body__(&data__->CLX_0148);
  CLX_0167_body__(&data__->CLX_0166);
  CLX_0153_body__(&data__->CLX_0152);
  CLX_0155_body__(&data__->CLX_0154);
  CLX_0157_body__(&data__->CLX_0156);
  CLX_0159_body__(&data__->CLX_0158);
  CLX_0161_body__(&data__->CLX_0160);
  CLX_0163_body__(&data__->CLX_0162);
  CLX_0165_body__(&data__->CLX_0164);
  CLX_0183_body__(&data__->CLX_0182);
  CLX_0169_body__(&data__->CLX_0168);
  CLX_0171_body__(&data__->CLX_0170);
  CLX_0173_body__(&data__->CLX_0172);
  CLX_0175_body__(&data__->CLX_0174);
  CLX_0177_body__(&data__->CLX_0176);
  CLX_0179_body__(&data__->CLX_0178);
  CLX_0181_body__(&data__->CLX_0180);
  CLX_0199_body__(&data__->CLX_0198);
  CLX_0185_body__(&data__->CLX_0184);
  CLX_0187_body__(&data__->CLX_0186);
  CLX_0189_body__(&data__->CLX_0188);
  CLX_0191_body__(&data__->CLX_0190);
  CLX_0193_body__(&data__->CLX_0192);
  CLX_0195_body__(&data__->CLX_0194);
  CLX_0197_body__(&data__->CLX_0196);
  CLX_0215_body__(&data__->CLX_0214);
  CLX_0201_body__(&data__->CLX_0200);
  CLX_0203_body__(&data__->CLX_0202);
  CLX_0205_body__(&data__->CLX_0204);
  CLX_0207_body__(&data__->CLX_0206);
  CLX_0209_body__(&data__->CLX_0208);
  CLX_0211_body__(&data__->CLX_0210);
  CLX_0213_body__(&data__->CLX_0212);
  CLX_0217_body__(&data__->CLX_0216);
  CLX_0219_body__(&data__->CLX_0218);
  CLX_0003_body__(&data__->CLX_0002);

  goto __end;

__end:
  return;
} // CLX_0001_body__() 





