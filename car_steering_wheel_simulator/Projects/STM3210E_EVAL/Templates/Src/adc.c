#include "adc.h"

ADC_HandleTypeDef hadc1; 

void HAL_USER_ADC_Init(void)
{
  ADC_ChannelConfTypeDef sConfig = {0};

  hadc1.Instance = ADC1;
  hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;             
  hadc1.Init.ContinuousConvMode = DISABLE;              
  hadc1.Init.DiscontinuousConvMode = DISABLE;            
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;       
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.NbrOfConversion = 1; 

  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    while(1); 
  }

  sConfig.Channel = ADC_CHANNEL_14;        
  sConfig.Rank = ADC_REGULAR_RANK_1;      
  sConfig.SamplingTime = ADC_SAMPLETIME_71CYCLES_5;
  
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    while(1);
  }

  HAL_ADCEx_Calibration_Start(&hadc1);
}

uint16_t HAL_USER_ADC_GetVolt(void)
{
  uint16_t rawValue = 0;

  HAL_ADC_Start(&hadc1);

  if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK)
  {
    rawValue = HAL_ADC_GetValue(&hadc1); 
  }

  HAL_ADC_Stop(&hadc1);

  return (uint16_t)COMPUTATION_DIGITAL_12BITS_TO_VOLTAGE(rawValue);
}