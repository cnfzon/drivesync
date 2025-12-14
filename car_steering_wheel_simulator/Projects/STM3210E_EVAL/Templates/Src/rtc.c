#include "rtc.h"

RTC_HandleTypeDef hrtc;

void HAL_RTC_MspInit(RTC_HandleTypeDef *hrtc)
{
  RCC_OscInitTypeDef        RCC_OscInitStruct = {0};
  RCC_PeriphCLKInitTypeDef  PeriphClkInitStruct = {0};
  
  __HAL_RCC_PWR_CLK_ENABLE();
  HAL_PWR_EnableBkUpAccess();

  __HAL_RCC_BKP_CLK_ENABLE();

#ifdef RTC_CLOCK_SOURCE_LSE
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_LSI | RCC_OSCILLATORTYPE_LSE;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  RCC_OscInitStruct.LSEState = RCC_LSE_ON; 
  RCC_OscInitStruct.LSIState = RCC_LSI_OFF; 
  
  if(HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  { 
    while(1); 
  }
  
  PeriphClkInitStruct.PeriphClockSelection = RCC_PERIPHCLK_RTC;
  PeriphClkInitStruct.RTCClockSelection = RCC_RTCCLKSOURCE_LSE;
  if(HAL_RCCEx_PeriphCLKConfig(&PeriphClkInitStruct) != HAL_OK)
  { 
    while(1);
  }

#elif defined (RTC_CLOCK_SOURCE_LSI)  

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_LSI | RCC_OSCILLATORTYPE_LSE;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  RCC_OscInitStruct.LSIState = RCC_LSI_ON;  
  RCC_OscInitStruct.LSEState = RCC_LSE_OFF;
  
  if(HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  { 
    while(1);
  }

  PeriphClkInitStruct.PeriphClockSelection = RCC_PERIPHCLK_RTC;
  PeriphClkInitStruct.RTCClockSelection = RCC_RTCCLKSOURCE_LSI;
  if(HAL_RCCEx_PeriphCLKConfig(&PeriphClkInitStruct) != HAL_OK)
  { 
    while(1);
  }
#else
  #error "Please select the RTC Clock source inside user_rtc.h file"
#endif 
  
  __HAL_RCC_RTC_ENABLE(); 
}

void HAL_RTC_MspDeInit(RTC_HandleTypeDef *hrtc)
{
  __HAL_RCC_RTC_DISABLE();
}

void HAL_USER_RTC_Init(void)
{
  hrtc.Instance = RTC;
  hrtc.Init.AsynchPrediv = RTC_AUTO_1_SECOND;
  hrtc.Init.OutPut = RTC_OUTPUTSOURCE_NONE;
  
  if (HAL_RTC_Init(&hrtc) != HAL_OK)
  {
    while(1);
  }
}

void HAL_USER_RTC_SetTimeDate(uint8_t year, uint8_t month, uint8_t date, uint8_t weekDay, uint8_t hour, uint8_t min, uint8_t sec)
{
  RTC_TimeTypeDef sTime = {0};
  RTC_DateTypeDef sDate = {0};

  sTime.Hours = hour;
  sTime.Minutes = min;
  sTime.Seconds = sec;
  HAL_RTC_SetTime(&hrtc, &sTime, RTC_FORMAT_BIN);

  sDate.WeekDay = weekDay;
  sDate.Month = month;
  sDate.Date = date;
  sDate.Year = year;
  HAL_RTC_SetDate(&hrtc, &sDate, RTC_FORMAT_BIN);
}

void HAL_USER_RTC_GetTime(uint8_t *hour, uint8_t *min, uint8_t *sec)
{
  RTC_TimeTypeDef sTime = {0};
  RTC_DateTypeDef sDate = {0};
  
  HAL_RTC_GetTime(&hrtc, &sTime, RTC_FORMAT_BIN);
  HAL_RTC_GetDate(&hrtc, &sDate, RTC_FORMAT_BIN);
  
  *hour = sTime.Hours;
  *min  = sTime.Minutes;
  *sec  = sTime.Seconds;
}

void HAL_USER_RTC_GetDate(uint8_t *year, uint8_t *month, uint8_t *date, uint8_t *weekDay)
{
  RTC_TimeTypeDef sTime = {0};
  RTC_DateTypeDef sDate = {0};

  HAL_RTC_GetTime(&hrtc, &sTime, RTC_FORMAT_BIN);
  HAL_RTC_GetDate(&hrtc, &sDate, RTC_FORMAT_BIN);
  
  *year    = sDate.Year;
  *month   = sDate.Month;
  *date    = sDate.Date;
  *weekDay = sDate.WeekDay;
}