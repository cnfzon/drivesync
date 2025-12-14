#include "gpio.h"

volatile int16_t g_EncoderValue = 0;
volatile int16_t g_EncoderIndex = 0;

static GPIO_InitTypeDef  GPIO_InitStruct;

void HAL_USER_GPIO_Init(void)
{
  /* -1- Enable each GPIO Clock */
  LED1_GPIO_CLK_ENABLE();
  LED2_GPIO_CLK_ENABLE();
  LED3_GPIO_CLK_ENABLE();
  LED4_GPIO_CLK_ENABLE();
  
  WAKEUP_BUTTON_GPIO_CLK_ENABLE();
  TAMPER_BUTTON_GPIO_CLK_ENABLE();
  
  UP_JOY_GPIO_CLK_ENABLE();
  DOWN_JOY_GPIO_CLK_ENABLE();
  LEFT_JOY_GPIO_CLK_ENABLE();
  RIGHT_JOY_GPIO_CLK_ENABLE();
  
  __GPIOB_CLK_ENABLE(); 
  __GPIOA_CLK_ENABLE();

  /* -2- Configure LEDs */
  GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull  = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;

  GPIO_InitStruct.Pin = LED1_PIN;
  HAL_GPIO_Init(LED1_GPIO_PORT, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = LED2_PIN;
  HAL_GPIO_Init(LED2_GPIO_PORT, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = LED3_PIN;
  HAL_GPIO_Init(LED3_GPIO_PORT, &GPIO_InitStruct);

  GPIO_InitStruct.Pin = LED4_PIN;
  HAL_GPIO_Init(LED4_GPIO_PORT, &GPIO_InitStruct);

  /* -3- Configure Buttons (Wakeup, Tamper) */
  GPIO_InitStruct.Mode  = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull  = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  
  GPIO_InitStruct.Pin = WAKEUP_BUTTON_PIN;
  HAL_GPIO_Init(WAKEUP_BUTTON_GPIO_PORT, &GPIO_InitStruct);
  
  GPIO_InitStruct.Pull  = GPIO_PULLUP;
  GPIO_InitStruct.Pin = TAMPER_BUTTON_PIN;
  HAL_GPIO_Init(TAMPER_BUTTON_GPIO_PORT, &GPIO_InitStruct);
  
  /* -4- Configure Joystick (GPIOB Pins) */
  GPIO_InitStruct.Pin = GPIO_PIN_15 | GPIO_PIN_14 | GPIO_PIN_13 | GPIO_PIN_12;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
  
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  GPIO_InitStruct.Pin = GPIO_PIN_7 | GPIO_PIN_6;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Pin = GPIO_PIN_2;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  HAL_NVIC_SetPriority(EXTI2_IRQn, 2, 0);
  HAL_NVIC_EnableIRQ(EXTI2_IRQn);
	
	HAL_NVIC_SetPriority(EXTI9_5_IRQn, 2, 0);
  HAL_NVIC_EnableIRQ(EXTI9_5_IRQn);
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
  if(GPIO_Pin == GPIO_PIN_2)
  {
    if(ENC_B) 
    {
      g_EncoderValue--;
    }
    else
    {
      g_EncoderValue++;
    }
  }
	else if(GPIO_Pin == GPIO_PIN_6)
  {
		g_EncoderIndex++;
	}
}

int16_t HAL_USER_GetEncoderValue(void)
{
  return g_EncoderValue;
}

int16_t HAL_USER_GetEncoderIndex(void)
{
  return g_EncoderIndex;
}