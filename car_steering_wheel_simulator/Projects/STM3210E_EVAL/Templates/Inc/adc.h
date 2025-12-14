#ifndef __ADC_H
#define __ADC_H

#include "main.h"

#define VDD_APPLI                      ((uint32_t) 3300)  
#define RANGE_12BITS                   ((uint32_t) 4095) 

#define COMPUTATION_DIGITAL_12BITS_TO_VOLTAGE(ADC_DATA) \
  ( (ADC_DATA) * VDD_APPLI / RANGE_12BITS)

void HAL_USER_ADC_Init(void);
uint16_t HAL_USER_ADC_GetVolt(void);

#endif /* __ADC_H */