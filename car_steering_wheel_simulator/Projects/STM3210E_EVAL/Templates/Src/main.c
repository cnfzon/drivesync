/**
  ******************************************************************************
  * @file    GPIO/GPIO_IOToggle/Src/main.c
  * @author  MCD Application Team
  * @version V1.4.0
  * @date    29-April-2016
  * @brief   This example describes how to configure and use GPIOs through
  *          the STM32F1xx HAL API.
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; COPYRIGHT(c) 2016 STMicroelectronics</center></h2>
  *
  * Redistribution and use in source and binary forms, with or without modification,
  * are permitted provided that the following conditions are met:
  *   1. Redistributions of source code must retain the above copyright notice,
  *      this list of conditions and the following disclaimer.
  *   2. Redistributions in binary form must reproduce the above copyright notice,
  *      this list of conditions and the following disclaimer in the documentation
  *      and/or other materials provided with the distribution.
  *   3. Neither the name of STMicroelectronics nor the names of its contributors
  *      may be used to endorse or promote products derived from this software
  *      without specific prior written permission.
  *
  * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
  * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
  * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
  * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
  * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
  * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
  *
  ******************************************************************************
  */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "gpio.h"
#include "uart.h"
#include "lcd.h"
#include "stdio.h"
#include "adc.h"
#include "rtc.h"
#include "stdint.h"

/* Private typedef -----------------------------------------------------------*/
/* Private define ------------------------------------------------------------*/
/* Private macro -------------------------------------------------------------*/
/* Private variables ---------------------------------------------------------*/

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);

#define IDLE_RPM        0.0f   
#define MAX_RPM         8000.0f  
#define ACCEL_RATE      0.2f     
#define BRAKE_RATE      0.8f     
#define FRICTION_RATE   0.1f     

const float GEAR_MAX_SPEED[] = {0, 40, 70, 110, 150, 190, 240, 280, 320};

typedef struct {
    float current_kmh; 
    int16_t out_rpm;   
    int16_t out_kmh;  
} CarPhysics_t;

static CarPhysics_t myCar = {0.0f, 0, 0};

void Car_UpdatePhysics(uint8_t throttle, uint8_t brake, uint8_t gear)
{
    float target_rpm = 0;
    
    if (gear > 8) gear = 8;

    if (gear == 0)
    {
        target_rpm = IDLE_RPM + ((float)throttle / 255.0f) * (MAX_RPM - IDLE_RPM);
        
        myCar.out_rpm += (target_rpm - myCar.out_rpm) * 0.1f;
        
        if (myCar.current_kmh > 0) myCar.current_kmh -= FRICTION_RATE;
        if (brake > 0) myCar.current_kmh -= (float)brake / 255.0f * BRAKE_RATE;
        if (myCar.current_kmh < 0) myCar.current_kmh = 0;
    }
    else 
    {
        if (throttle > 0) myCar.current_kmh += ((float)throttle / 255.0f) * ACCEL_RATE;
        else 							myCar.current_kmh -= FRICTION_RATE;

        if (brake > 0)		myCar.current_kmh -= ((float)brake / 255.0f) * BRAKE_RATE;

        if (myCar.current_kmh < 0) myCar.current_kmh = 0;
        
        if (myCar.current_kmh > GEAR_MAX_SPEED[gear]) myCar.current_kmh = GEAR_MAX_SPEED[gear];

        float ratio = myCar.current_kmh / GEAR_MAX_SPEED[gear];
        target_rpm = ratio * MAX_RPM;

        if (target_rpm < IDLE_RPM) target_rpm = IDLE_RPM;
        
        myCar.out_rpm = (int16_t)target_rpm;
    }
    
    myCar.out_kmh = (int16_t)myCar.current_kmh;
}

int16_t Get_Sim_RPM(void) { return myCar.out_rpm; }
int16_t Get_Sim_KMH(void) { return myCar.out_kmh; }

int8_t mode_buf = -1;
int8_t mode     = 0;

uint8_t  car_gear = 0;
uint16_t car_rpm = 0;
uint16_t car_speed = 0;
uint8_t  car_throttle = 0;
uint8_t  car_brake = 0;
int16_t  car_steer_angle = 0;

uint8_t enc_a = 0;
uint8_t enc_b = 0;
uint8_t enc_i = 0;
int16_t enc_value = 0;
int16_t enc_offset = 0;
int16_t enc_sensitive = 0;

uint8_t left_trig = 0;
uint8_t right_trig = 0;
uint8_t left_btn = 0;
uint8_t right_btn = 0;

uint8_t lcd_buf[20];

uint16_t adc_volt = 0;

uint8_t system_hour = 0;
uint8_t system_min = 0;
uint8_t system_sec = 0;

void Car_Info_To_UART(uint8_t gear, uint16_t rpm, uint16_t speed, uint8_t throttle, uint8_t brake, int16_t steer_angle)
{	
	uint8_t uart_buf[17];
	
	uart_buf[0] = 0xAB;
	uart_buf[1] = '.';
	uart_buf[2] = gear & 0xFF;
	uart_buf[3] = '.';
	uart_buf[4] = (rpm >> 8) & 0xFF; 
	uart_buf[5] = rpm & 0xFF;
	uart_buf[6] = '.'; 
	uart_buf[7] = (speed >> 8) & 0xFF; 
	uart_buf[8] = speed & 0xFF;
	uart_buf[9] = '.'; 
	uart_buf[10] = throttle & 0xFF;
	uart_buf[11] = '.'; 
	uart_buf[12] = brake & 0xFF;
	uart_buf[13] = '.'; 
	uart_buf[14] = (steer_angle >> 8) & 0xFF; 
	uart_buf[15] = steer_angle & 0xFF;
	
	for(uint8_t i=0; i<16; i++)
		HAL_UART_Transmit(&UartHandle, &uart_buf[i], 1, 0xFFFF);
}


/* Private functions ---------------------------------------------------------*/

void Task0(void)
{
	LCD_Draw_ST_Logo(); HAL_Delay(500);
	for(uint8_t i=0; i<4; i++)
	{
		LED4((i == 0) ? 1 : 0);
		LED3((i == 1) ? 1 : 0);
		LED2((i == 2) ? 1 : 0);
		LED1((i == 3) ? 1 : 0);
		HAL_Delay(100);
	}
	for(uint8_t i=0; i<7; i++)
	{
		LED4((i % 2) ? 1 : 0);
		LED3((i % 2) ? 1 : 0);
		LED2((i % 2) ? 1 : 0);
		LED1((i % 2) ? 1 : 0);
		HAL_Delay(100);
	}
	LCD_Clear();
}

void Developer_Mode(void)
{
	while(1)
	{
		static uint8_t is_first_flag = 1;
		static uint32_t system_time = 0;
		static uint8_t page = 0;
		static uint8_t tamper_last = 1;
		static uint8_t wakeup_last = 1;
		
		HAL_USER_RTC_GetTime(&system_hour, &system_min, &system_sec);
		
		enc_value = HAL_USER_GetEncoderValue();
		
		if(WAKE_UP != wakeup_last)
		{
			wakeup_last = WAKE_UP;
			
			if(WAKE_UP == 0) enc_offset = enc_value;
		}
		
		if(is_first_flag == 0)
		{
			if(TAMPER != tamper_last)
			{
				tamper_last = TAMPER;
				
				if(TAMPER == 1)
					page = !page;
			}
			
			if(HAL_GetTick() - system_time > 300)
			{
				system_time = HAL_GetTick();
				
				switch(page)
				{
					case 0:
						LCD_DrawString_Text(0, 0, " Developer_Mode ");
						sprintf(lcd_buf, " Time: %02d:%02d:%02d ", system_hour, system_min, system_sec);
						LCD_DrawString_Text(2, 0, lcd_buf);
						sprintf(lcd_buf, " LT:%3s  RT:%3s ", (LEFT_TRIG ? "Hi" : "Lo"), (RIGHT_TRIG ? "Hi" : "Lo"));
						LCD_DrawString_Text(4, 0, lcd_buf);
						sprintf(lcd_buf, " LB:%3s  RB:%3s ", (LEFT_BTN ? "Hi" : "Lo"), (RIGHT_BTN ? "Hi" : "Lo"));
						LCD_DrawString_Text(6, 0, lcd_buf);
					break;
					
					case 1:
						LCD_DrawString_Text(0, 0, " Developer_Mode ");
						sprintf(lcd_buf, "ENC Value: %5d", enc_value);
						LCD_DrawString_Text(2, 0, lcd_buf);
						sprintf(lcd_buf, "ENC Offset:%5d", enc_offset);
						LCD_DrawString_Text(4, 0, lcd_buf);
						sprintf(lcd_buf, "  VR1: %4d mV ", HAL_USER_ADC_GetVolt());
						LCD_DrawString_Text(6, 0, lcd_buf);
					break;	
				}
			}
		}
		else
		{
			is_first_flag = 0;
			system_time = HAL_GetTick() + 300;
		}
	}
}

void Normal_Mode(void)
{
	while(1)
	{
		static uint8_t is_first_flag = 1;
		static uint32_t cnt_300ms = 0;
		static uint32_t cnt_1ms = 0;
		static uint32_t cnt_50ms = 0;
		static uint32_t cnt_1500ms = 0;
		static uint32_t press_cnt = 0;
		static uint8_t page = 0;
		static uint8_t is_init = 1;
		static uint8_t tamper_last = 1;
		static uint8_t wakeup_last = 1;
		static uint8_t start_blink = 0;
		static uint16_t adc_volt_last = 0;
		
		HAL_USER_RTC_GetTime(&system_hour, &system_min, &system_sec);
		
		enc_value = HAL_USER_GetEncoderValue();
		
		if(is_first_flag == 0)
		{
			if(is_init)
			{
					if(HAL_GetTick() - cnt_300ms > 300)
					{
						cnt_300ms = HAL_GetTick();
						LCD_DrawString_Text(0, 0, "  Driver_SYMC  ");
						sprintf(lcd_buf, "   %02d:%02d:%02d   ", system_hour, system_min, system_sec);
						LCD_DrawString_Text(2, 0, lcd_buf);
						
						if((HAL_GetTick() - press_cnt) <= 200)	
						{
							sprintf(lcd_buf, "                    ");
							LCD_DrawString_Text(4, 0, lcd_buf);	
						}
						
						if(start_blink)	sprintf(lcd_buf, "  Engine Start  "); 
						else						sprintf(lcd_buf, "                ");
						LCD_DrawString_Text(6, 0, lcd_buf);
					}
					
					if(WAKE_UP == 1)
					{
						start_blink = 1;
						for(uint8_t i=1; i<15; i++)
						{
							if(i < (HAL_GetTick() - press_cnt) / 230)
								lcd_buf[i] = '-';
							else
								lcd_buf[i] = ' ';
							
						}
						
						LED4(((HAL_GetTick() - press_cnt) / 230 > 3) ? 1 : 0);
						LED3(((HAL_GetTick() - press_cnt) / 230 > 6) ? 1 : 0);
						LED2(((HAL_GetTick() - press_cnt) / 230 > 9) ? 1 : 0);
						LED1(((HAL_GetTick() - press_cnt) / 230 > 12) ? 1 : 0);
						
						lcd_buf[0] = ' ';
						
						LCD_DrawString_Text(4, 0, lcd_buf);	
						if(HAL_GetTick() - press_cnt >= 3500)
						{
							is_init = 0;
							enc_offset = HAL_USER_GetEncoderValue();
							adc_volt_last = HAL_USER_ADC_GetVolt();
							LCD_Clear();
							
							HAL_Delay(600);
							cnt_50ms = HAL_GetTick() + 50;
							cnt_1ms  = HAL_GetTick() + 1;

						}
					}
					else
					{
						press_cnt = HAL_GetTick();
						
						if(HAL_GetTick() - cnt_1500ms > 1500)
						{
							cnt_1500ms = HAL_GetTick();
							
							start_blink = !start_blink;
						}
					}
			}
			else
			{
				static uint8_t page = 0;
				static uint8_t tamper_last = 1;
				static uint8_t wakeup_last = 1;
				static uint8_t left_btn_last = 0;
				static uint8_t right_btn_last = 0;
				
				car_steer_angle = (enc_value - enc_offset) * (5.0 + (float)enc_sensitive / 10);
				
				LED4((car_rpm >= 1600) ? 1 : 0);
				LED3((car_rpm >= 3200) ? 1 : 0);
				LED2((car_rpm >= 4800) ? 1 : 0);
				LED1((car_rpm >= 6400) ? 1 : 0);
				
				if(page == 1)
				{
					if(WAKE_UP != wakeup_last)
					{
						wakeup_last = WAKE_UP;
						
						if(WAKE_UP == 0) enc_offset = enc_value;
					}

						enc_sensitive = (HAL_USER_ADC_GetVolt() - adc_volt_last) / 30;
				}

				
				if(HAL_GetTick() - cnt_1ms > 1)
				{
					cnt_1ms = HAL_GetTick();
					
					if((RIGHT_TRIG == 1) && (car_throttle < 255))
						car_throttle++;
					else if((RIGHT_TRIG == 0) && (car_throttle > 0))
						car_throttle--;

					if((LEFT_TRIG == 1) && (car_brake < 255))
						car_brake++;
					else if((LEFT_TRIG == 0) && (car_brake > 0))
						car_brake--;
					
					if(LEFT_BTN != left_btn_last)
					{
						left_btn_last = LEFT_BTN;
						if((LEFT_BTN == 1) && (car_gear > 0))
							car_gear--;
					}
					
					if(RIGHT_BTN != right_btn_last)
					{
						right_btn_last = RIGHT_BTN;
						if((RIGHT_BTN == 1) && (car_gear < 8))
								car_gear++;
					}		
					
					Car_UpdatePhysics(car_throttle, car_brake, car_gear);
					
					car_rpm = Get_Sim_RPM();
					car_speed = Get_Sim_KMH();
					
					Car_Info_To_UART(car_gear, car_rpm, car_speed, car_throttle, car_brake, car_steer_angle);
				}
				
				if(TAMPER != tamper_last)
				{
					tamper_last = TAMPER;
					cnt_50ms = HAL_GetTick() + 50;
					if(TAMPER)	page =! page;
				}
		
					if(HAL_GetTick() - cnt_50ms > 50)
					{
						cnt_50ms = HAL_GetTick();
						
						if(page == 0)
						{
							sprintf(lcd_buf, "Gear %1d  %02d:%02d:%02d", car_gear, system_hour, system_min, system_sec);
							LCD_DrawString_Text(0, 0, lcd_buf);
							sprintf(lcd_buf, "  Deg  %+3d.%1d    ", car_steer_angle / 10, (car_steer_angle >= 0 ? car_steer_angle : -car_steer_angle) % 10);
							LCD_DrawString_Text(2, 0, lcd_buf);
							sprintf(lcd_buf, "%4d RPM %3d Kmh", car_rpm, car_speed);
							LCD_DrawString_Text(4, 0, lcd_buf);
							sprintf(lcd_buf, "Brk %03d  Thr %03d", car_brake, car_throttle);
							LCD_DrawString_Text(6, 0, lcd_buf);
						}
						else
						{
							LCD_DrawString_Text(0, 0, "  Setting Mode  ");
							sprintf(lcd_buf, "Sensitive: %+3d.%d ", enc_sensitive / 10, (enc_sensitive >= 0 ? enc_sensitive : -enc_sensitive) % 10);
							LCD_DrawString_Text(2, 0, lcd_buf);
							sprintf(lcd_buf, "ENC Value: %5d", enc_value);
							LCD_DrawString_Text(4, 0, lcd_buf);
							sprintf(lcd_buf, "ENC Offset:%5d", enc_offset);
							LCD_DrawString_Text(6, 0, lcd_buf);
						}
					}

			}
		}
		else
		{
			is_first_flag = 0;
			cnt_300ms = HAL_GetTick() + 300;
			cnt_1500ms = HAL_GetTick() + 1500;
			press_cnt = HAL_GetTick();
		}
	}
}
/**
  * @brief  Main program
  * @param  None
  * @retval None
  */
int main(void)
{
  /* This sample code shows how to use GPIO HAL API to toggle LED1, LED2, LED3 and LED4 IOs
    in an infinite loop. */
	
  HAL_Init();

  /* Configure the system clock to 72 MHz */
  SystemClock_Config();
	
	LCD_Init();
	LCD_Clear();
	
	HAL_USER_GPIO_Init();
	HAL_USER_UART_Init();
	HAL_USER_ADC_Init();
	HAL_USER_RTC_Init();
	
	Task0();
	
	HAL_USER_RTC_SetTimeDate(0, 0, 0, 0, 0, 0, 0);
	
	if(WAKE_UP)	Developer_Mode();
	
	Normal_Mode();
	
  while (1)
  {		
		
  }
}

/**
  * @brief  System Clock Configuration
  *         The system Clock is configured as follow : 
  *            System Clock source            = PLL (HSE)
  *            SYSCLK(Hz)                     = 72000000
  *            HCLK(Hz)                       = 72000000
  *            AHB Prescaler                  = 1
  *            APB1 Prescaler                 = 2
  *            APB2 Prescaler                 = 1
  *            HSE Frequency(Hz)              = 8000000
  *            HSE PREDIV1                    = 1
  *            PLLMUL                         = 9
  *            Flash Latency(WS)              = 2
  * @param  None
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_ClkInitTypeDef clkinitstruct = {0};
  RCC_OscInitTypeDef oscinitstruct = {0};
  
  /* Enable HSE Oscillator and activate PLL with HSE as source */
  oscinitstruct.OscillatorType  = RCC_OSCILLATORTYPE_HSE;
  oscinitstruct.HSEState        = RCC_HSE_ON;
  oscinitstruct.HSEPredivValue  = RCC_HSE_PREDIV_DIV1;
  oscinitstruct.PLL.PLLState    = RCC_PLL_ON;
  oscinitstruct.PLL.PLLSource   = RCC_PLLSOURCE_HSE;
  oscinitstruct.PLL.PLLMUL      = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&oscinitstruct)!= HAL_OK)
  {
    /* Initialization Error */
    while(1);
  }

  /* Select PLL as system clock source and configure the HCLK, PCLK1 and PCLK2 
     clocks dividers */
  clkinitstruct.ClockType = (RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2);
  clkinitstruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  clkinitstruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  clkinitstruct.APB2CLKDivider = RCC_HCLK_DIV1;
  clkinitstruct.APB1CLKDivider = RCC_HCLK_DIV2;  
  if (HAL_RCC_ClockConfig(&clkinitstruct, FLASH_LATENCY_2)!= HAL_OK)
  {
    /* Initialization Error */
    while(1);
  }
}


#ifdef  USE_FULL_ASSERT

/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */

  /* Infinite loop */
  while (1)
  {
  }
}
#endif

/**
  * @}
  */

/**
  * @}
  */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
