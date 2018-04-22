close all
clear

%set these parameters 
time_step=15;%minutes
total_days=4;
%set the number of customers requiring power over the next four days
Number_customers_per_day=[30,20,15,10];
Number_flexible_customers=40; % 

%read appliance list:
Appliance_List=xlsread('Appliance_List.xlsx')
Appliance_List=Appliance_List(:,2);

%plot dist functions
%change the normpdf parameters as required, and update these below in the normrnd functions.
subplot(2,1,1)
x = [0:.01:24];
norm = normpdf(x,14,5);
area(x,norm)
grid on
xlabel('Start time of system use (24 hour time)')
ylabel('PDF')

subplot(2,1,2)
x = [0:.01:10];
norm = normpdf(x,2,2);
h=area(x,norm)
h(1).FaceColor = 'r';
xlabel('Number of hours use (h)')
ylabel('PDF')
grid on

figure
%create potential start times and usage hours based off a normal
%distribution
%
%Parameters of system from Jalel
%6kW solar 
%8kW inverter
%600Ah lead acid

%more customers need power around the 2pm mean, with SD 5:
Start_time = normrnd(14,5,1000,1);
%more customers need to use power for 2 hours, with SD 0.5
Number_of_hours = normrnd(2,.5,1000,1);
Start_time(find(Start_time>24|Start_time<=0))=[];
Number_of_hours(find(Number_of_hours>5|Number_of_hours<=0.5))=[];

Start_time_training=[]
Number_of_hours_training=[]
Number_of_flexible_hours_Training=[]

for i=1:length(Number_customers_per_day)
    I1=randperm(length(Start_time),Number_customers_per_day(i));
    I2=randperm(length(Number_of_hours),Number_customers_per_day(i));
    Start_time_training=[Start_time_training;(i-1)*24+sort(Start_time(I1))];
    Number_of_hours_training=[Number_of_hours_training;Number_of_hours(I2)];
    i
end

I3=randperm(length(Number_of_hours),Number_flexible_customers);
Number_of_flexible_hours_Training=Number_of_hours(I3);

%round to the nearest 15 min
Start_time_training=fix(Start_time_training/0.25)*0.25;
Number_of_hours_training=fix(Number_of_hours_training/0.25)*0.25;
Number_of_flexible_hours_Training=fix(Number_of_flexible_hours_Training/0.25)*0.25;
subplot(3,1,1)
plot((Start_time_training))
xlabel('Customer number')
grid on
ylabel('Start time, hour number over the 4 day period')
xlabel('Customer number Fixed')

subplot(3,1,2)
grid on
plot(sort(Number_of_hours_training))

ylabel('Number of hours use')
xlabel('Customer number Fixed')

grid on

subplot(3,1,3)
xlabel('Customer number')
grid on
plot(sort(Number_of_flexible_hours_Training))

ylabel('Number of hours use')
xlabel('Customer number Flexible')

grid on
%Customer k required appliance type i during interval h
%or integer if multiple appliances could be used. 
24*60/time_step
fixed_customer_requests=zeros(sum(Number_customers_per_day),length(Appliance_List),24*60/time_step*length(Number_customers_per_day));
flexible_customer_requests=zeros(sum(Number_flexible_customers),length(Appliance_List));
flexible_customer_hours_requests=zeros(sum(Number_flexible_customers),1);


for Flex_customers=1:sum(Number_flexible_customers)
    Appliance=randperm(length(Appliance_List),1);
    flexible_customer_requests(Flex_customers,Appliance)=1;
    flexible_customer_hours_requests(Flex_customers)=Number_of_flexible_hours_Training(Flex_customers)*60/time_step;
end


for customer=1:sum(Number_customers_per_day)
    
    Appliance=randperm(length(Appliance_List),1);
    fixed_customer_requests(customer,Appliance,(Start_time_training(customer)*60/time_step):((Start_time_training(customer)*60/time_step)+Number_of_hours_training(customer)*60/time_step))=1;
    
end
load SolarLochiel.mat
Solar = interp(Solar,2);
%plot(Solar)
% save('Testing_Data.mat','Solar','flexible_customer_hours_requests','flexible_customer_requests','fixed_customer_requests','Appliance_List')

