import datetime
import os
import re
import time
from threading import current_thread, Thread

from serial import SerialException
from config import ROOT_PATH
from utils import raise_error, sample_max_volume_reached_mb


class Reader:
    debug = False
    interpolation_data = None
    last_read = {}
    last_entry = {}
    log_file = None
    filename = None
    digits_after_dec = 2
    collect_samples = False
    layout = None
    sample_data = {
        "current_volume": 0.0,
        "current_sample": 1,
        "continue_sample": False,
        "start_time": 0
    }
    reading_list = ['0.01  g', '0.02  g', '0.03  g', '0.04  g', '0.05  g', '0.06  g', '0.07  g', '0.08  g', '0.09  g', '0.10  g', '0.12  g', '0.14  g', '0.16  g', '0.18  g', '0.20  g', '0.22  g', '0.24  g', '0.26  g', '0.28  g', '0.30  g', '0.33  g', '0.36  g', '0.39  g', '0.42  g', '0.45  g', '0.48  g', '0.51  g', '0.54  g', '0.57  g', '0.60  g', '0.64  g', '0.68  g', '0.72  g', '0.76  g', '0.80  g', '0.84  g', '0.88  g', '0.92  g', '0.96  g', '1.00  g', '1.05  g', '1.10  g', '1.15  g', '1.20  g', '1.25  g', '1.30  g', '1.35  g', '1.40  g', '1.45  g', '1.50  g', '1.56  g', '1.62  g', '1.68  g', '1.74  g', '1.80  g', '1.86  g', '1.92  g', '1.98  g', '2.04  g', '2.10  g', '2.17  g', '2.24  g', '2.31  g', '2.38  g', '2.45  g', '2.52  g', '2.59  g', '2.66  g', '2.73  g', '2.80  g', '2.88  g', '2.96  g', '3.04  g', '3.12  g', '3.20  g', '3.28  g', '3.36  g', '3.44  g', '3.52  g', '3.60  g', '3.69  g', '3.78  g', '3.87  g', '3.96  g', '4.05  g', '4.14  g', '4.23  g', '4.32  g', '4.41  g', '4.50  g', '4.60  g', '4.70  g', '4.80  g', '4.90  g', '5.00  g', '5.10  g', '5.20  g', '5.30  g', '5.40  g', '5.50  g', '5.61  g', '5.72  g', '5.83  g', '5.94  g', '6.05  g', '6.16  g', '6.27  g', '6.38  g', '6.49  g', '6.60  g', '6.72  g', '6.84  g', '6.96  g', '7.08  g', '7.20  g', '7.32  g', '7.44  g', '7.56  g', '7.68  g', '7.80  g', '7.93  g', '8.06  g', '8.19  g', '8.32  g', '8.45  g', '8.58  g', '8.71  g', '8.84  g', '8.97  g', '9.10  g', '9.24  g', '9.38  g', '9.52  g', '9.66  g', '9.80  g', '9.94  g', '10.08  g', '10.22  g', '10.36  g', '10.50  g', '10.65  g', '10.80  g', '10.95  g', '11.10  g', '11.25  g', '11.40  g', '11.55  g', '11.70  g', '11.85  g', '12.00  g', '12.16  g', '12.32  g', '12.48  g', '12.64  g', '12.80  g', '12.96  g', '13.12  g', '13.28  g', '13.44  g', '13.60  g', '13.77  g', '13.94  g', '14.11  g', '14.28  g', '14.45  g', '14.62  g', '14.79  g', '14.96  g', '15.13  g', '15.30  g', '15.48  g', '15.66  g', '15.84  g', '16.02  g', '16.20  g', '16.38  g', '16.56  g', '16.74  g', '16.92  g', '17.10  g', '17.29  g', '17.48  g', '17.67  g', '17.86  g', '18.05  g', '18.24  g', '18.43  g', '18.62  g', '18.81  g', '19.00  g', '19.20  g', '19.40  g', '19.60  g', '19.80  g', '20.00  g', '20.20  g', '20.40  g', '20.60  g', '20.80  g', '21.00  g', '21.21  g', '21.42  g', '21.63  g', '21.84  g', '22.05  g', '22.26  g', '22.47  g', '22.68  g', '22.89  g', '23.10  g', '23.32  g', '23.54  g', '23.76  g', '23.98  g', '24.20  g', '24.42  g', '24.64  g', '24.86  g', '25.08  g', '25.30  g', '25.53  g', '25.76  g', '25.99  g', '26.22  g', '26.45  g', '26.68  g', '26.91  g', '27.14  g', '27.37  g', '27.60  g', '27.84  g', '28.08  g', '28.32  g', '28.56  g', '28.80  g', '29.04  g', '29.28  g', '29.52  g', '29.76  g', '30.00  g', '30.25  g', '30.50  g', '30.75  g', '31.00  g', '31.25  g', '31.50  g', '31.75  g', '32.00  g', '32.25  g', '32.50  g', '32.76  g', '33.02  g', '33.28  g', '33.54  g', '33.80  g', '34.06  g', '34.32  g', '34.58  g', '34.84  g', '35.10  g', '35.37  g', '35.64  g', '35.91  g', '36.18  g', '36.45  g', '36.72  g', '36.99  g', '37.26  g', '37.53  g', '37.80  g', '38.08  g', '38.36  g', '38.64  g', '38.92  g', '39.20  g', '39.48  g', '39.76  g', '40.04  g', '40.32  g', '40.60  g', '40.89  g', '41.18  g', '41.47  g', '41.76  g', '42.05  g', '42.34  g', '42.63  g', '42.92  g', '43.21  g', '43.50  g', '43.80  g', '44.10  g', '44.40  g', '44.70  g', '45.00  g', '45.30  g', '45.60  g', '45.90  g', '46.20  g', '46.50  g', '46.81  g', '47.12  g', '47.43  g', '47.74  g', '48.05  g', '48.36  g', '48.67  g', '48.98  g', '49.29  g', '49.60  g', '49.92  g', '50.24  g', '50.56  g', '50.88  g', '51.20  g', '51.52  g', '51.84  g', '52.16  g', '52.48  g', '52.80  g', '53.13  g', '53.46  g', '53.79  g', '54.12  g', '54.45  g', '54.78  g', '55.11  g', '55.44  g', '55.77  g', '56.10  g', '56.44  g', '56.78  g', '57.12  g', '57.46  g', '57.80  g', '58.14  g', '58.48  g', '58.82  g', '59.16  g', '59.50  g', '59.85  g', '60.20  g', '60.55  g', '60.90  g', '61.25  g', '61.60  g', '61.95  g', '62.30  g', '62.65  g', '63.00  g', '63.36  g', '63.72  g', '64.08  g', '64.44  g', '64.80  g', '65.16  g', '65.52  g', '65.88  g', '66.24  g', '66.60  g', '66.97  g', '67.34  g', '67.71  g', '68.08  g', '68.45  g', '68.82  g', '69.19  g', '69.56  g', '69.93  g', '70.30  g', '70.68  g', '71.06  g', '71.44  g', '71.82  g', '72.20  g', '72.58  g', '72.96  g', '73.34  g', '73.72  g', '74.10  g', '74.49  g', '74.88  g', '75.27  g', '75.66  g', '76.05  g', '76.44  g', '76.83  g', '77.22  g', '77.61  g', '78.00  g', '78.40  g', '78.80  g', '79.20  g', '79.60  g', '80.00  g', '80.40  g', '80.80  g', '81.20  g', '81.60  g', '82.00  g', '82.41  g', '82.82  g', '83.23  g', '83.64  g', '84.05  g', '84.46  g', '84.87  g', '85.28  g', '85.69  g', '86.10  g', '86.52  g', '86.94  g', '87.36  g', '87.78  g', '88.20  g', '88.62  g', '89.04  g', '89.46  g', '89.88  g', '90.30  g', '90.73  g', '91.16  g', '91.59  g', '92.02  g', '92.45  g', '92.88  g', '93.31  g', '93.74  g', '94.17  g', '94.60  g', '95.04  g', '95.48  g', '95.92  g', '96.36  g', '96.80  g', '97.24  g', '97.68  g', '98.12  g', '98.56  g', '99.00  g', '99.45  g', '99.90  g', '100.35  g', '100.80  g', '101.25  g', '101.70  g', '102.15  g', '102.60  g', '103.05  g', '103.50  g', '103.96  g', '104.42  g', '104.88  g', '105.34  g', '105.80  g', '106.26  g', '106.72  g', '107.18  g', '107.64  g', '108.10  g', '108.57  g', '109.04  g', '109.51  g', '109.98  g', '110.45  g', '110.92  g', '111.39  g', '111.86  g', '112.33  g', '112.80  g', '113.28  g', '113.76  g', '114.24  g', '114.72  g', '115.20  g', '115.68  g', '116.16  g', '116.64  g', '117.12  g', '117.60  g', '118.09  g', '118.58  g', '119.07  g', '119.56  g', '120.05  g', '120.54  g', '121.03  g', '121.52  g', '122.01  g', '122.50  g', '123.00  g', '123.50  g', '124.00  g', '124.50  g', '125.00  g', '125.50  g', '126.00  g', '126.50  g', '127.00  g', '127.50  g', '128.01  g', '128.52  g', '129.03  g', '129.54  g', '130.05  g', '130.56  g', '131.07  g', '131.58  g', '132.09  g', '132.60  g', '133.12  g', '133.64  g', '134.16  g', '134.68  g', '135.20  g', '135.72  g', '136.24  g', '136.76  g', '137.28  g', '137.80  g', '138.33  g', '138.86  g', '139.39  g', '139.92  g', '140.45  g', '140.98  g', '141.51  g', '142.04  g', '142.57  g', '143.10  g', '143.64  g', '144.18  g', '144.72  g', '145.26  g', '145.80  g', '146.34  g', '146.88  g', '147.42  g', '147.96  g', '148.50  g', '149.05  g', '149.60  g', '150.15  g', '150.70  g', '151.25  g', '151.80  g', '152.35  g', '152.90  g', '153.45  g', '154.00  g', '154.56  g', '155.12  g', '155.68  g', '156.24  g', '156.80  g', '157.36  g', '157.92  g', '158.48  g', '159.04  g', '159.60  g', '160.17  g', '160.74  g', '161.31  g', '161.88  g', '162.45  g', '163.02  g', '163.59  g', '164.16  g', '164.73  g', '165.30  g', '165.88  g', '166.46  g', '167.04  g', '167.62  g', '168.20  g', '168.78  g', '169.36  g', '169.94  g', '170.52  g', '171.10  g', '171.69  g', '172.28  g', '172.87  g', '173.46  g', '174.05  g', '174.64  g', '175.23  g', '175.82  g', '176.41  g', '177.00  g', '177.60  g', '178.20  g', '178.80  g', '179.40  g', '180.00  g', '180.60  g', '181.20  g', '181.80  g', '182.40  g', '183.00  g', '183.61  g', '184.22  g', '184.83  g', '185.44  g', '186.05  g', '186.66  g', '187.27  g', '187.88  g', '188.49  g', '189.10  g', '189.72  g', '190.34  g', '190.96  g', '191.58  g', '192.20  g', '192.82  g', '193.44  g', '194.06  g', '194.68  g', '195.30  g', '195.93  g', '196.56  g', '197.19  g', '197.82  g', '198.45  g', '199.08  g', '199.71  g', '200.34  g', '200.97  g', '201.60  g', '202.24  g', '202.88  g', '203.52  g', '204.16  g', '204.80  g', '205.44  g', '206.08  g', '206.72  g', '207.36  g', '208.00  g', '208.65  g', '209.30  g', '209.95  g', '210.60  g', '211.25  g', '211.90  g', '212.55  g', '213.20  g', '213.85  g', '214.50  g', '215.16  g', '215.82  g', '216.48  g', '217.14  g', '217.80  g', '218.46  g', '219.12  g', '219.78  g', '220.44  g', '221.10  g', '221.77  g', '222.44  g', '223.11  g', '223.78  g', '224.45  g', '225.12  g', '225.79  g', '226.46  g', '227.13  g', '227.80  g', '228.48  g', '229.16  g', '229.84  g', '230.52  g', '231.20  g', '231.88  g', '232.56  g', '233.24  g', '233.92  g', '234.60  g', '235.29  g', '235.98  g', '236.67  g', '237.36  g', '238.05  g', '238.74  g', '239.43  g', '240.12  g', '240.81  g', '241.50  g', '242.20  g', '242.90  g', '243.60  g', '244.30  g', '245.00  g', '245.70  g', '246.40  g', '247.10  g', '247.80  g', '248.50  g', '249.21  g', '249.92  g', '250.63  g', '251.34  g', '252.05  g', '252.76  g', '253.47  g', '254.18  g', '254.89  g', '255.60  g', '256.32  g', '257.04  g', '257.76  g', '258.48  g', '259.20  g', '259.92  g', '260.64  g', '261.36  g', '262.08  g', '262.80  g', '263.53  g', '264.26  g', '264.99  g', '265.72  g', '266.45  g', '267.18  g', '267.91  g', '268.64  g', '269.37  g', '270.10  g', '270.84  g', '271.58  g', '272.32  g', '273.06  g', '273.80  g', '274.54  g', '275.28  g', '276.02  g', '276.76  g', '277.50  g', '278.25  g', '279.00  g', '279.75  g', '280.50  g', '281.25  g', '282.00  g', '282.75  g', '283.50  g', '284.25  g', '285.00  g', '285.76  g', '286.52  g', '287.28  g', '288.04  g', '288.80  g', '289.56  g', '290.32  g', '291.08  g', '291.84  g', '292.60  g', '293.37  g', '294.14  g', '294.91  g', '295.68  g', '296.45  g', '297.22  g', '297.99  g', '298.76  g', '299.53  g', '300.30  g', '301.08  g', '301.86  g', '302.64  g', '303.42  g', '304.20  g', '304.98  g', '305.76  g', '306.54  g', '307.32  g', '308.10  g', '308.89  g', '309.68  g', '310.47  g', '311.26  g', '312.05  g', '312.84  g', '313.63  g', '314.42  g', '315.21  g', '316.00  g', '316.80  g', '317.60  g', '318.40  g', '319.20  g', '320.00  g', '320.80  g', '321.60  g', '322.40  g', '323.20  g', '324.00  g', '324.81  g', '325.62  g', '326.43  g', '327.24  g', '328.05  g', '328.86  g', '329.67  g', '330.48  g', '331.29  g', '332.10  g', '332.92  g', '333.74  g', '334.56  g', '335.38  g', '336.20  g', '337.02  g', '337.84  g', '338.66  g', '339.48  g', '340.30  g', '341.13  g', '341.96  g', '342.79  g', '343.62  g', '344.45  g', '345.28  g', '346.11  g', '346.94  g', '347.77  g', '348.60  g', '349.44  g', '350.28  g', '351.12  g', '351.96  g', '352.80  g', '353.64  g', '354.48  g', '355.32  g', '356.16  g', '357.00  g', '357.85  g', '358.70  g', '359.55  g', '360.40  g', '361.25  g', '362.10  g', '362.95  g', '363.80  g', '364.65  g', '365.50  g', '366.36  g', '367.22  g', '368.08  g', '368.94  g', '369.80  g', '370.66  g', '371.52  g', '372.38  g', '373.24  g', '374.10  g', '374.97  g', '375.84  g', '376.71  g', '377.58  g', '378.45  g', '379.32  g', '380.19  g', '381.06  g', '381.93  g', '382.80  g', '383.68  g', '384.56  g', '385.44  g', '386.32  g', '387.20  g', '388.08  g', '388.96  g', '389.84  g', '390.72  g', '391.60  g', '392.49  g', '393.38  g', '394.27  g', '395.16  g', '396.05  g', '396.94  g', '397.83  g', '398.72  g', '399.61  g', '400.50  g', '401.40  g', '402.30  g', '403.20  g', '404.10  g', '405.00  g', '405.90  g', '406.80  g', '407.70  g', '408.60  g', '409.50  g', '410.41  g', '411.32  g', '412.23  g', '413.14  g', '414.05  g', '414.96  g', '415.87  g', '416.78  g', '417.69  g', '418.60  g', '419.52  g', '420.44  g', '421.36  g', '422.28  g', '423.20  g', '424.12  g', '425.04  g', '425.96  g', '426.88  g', '427.80  g', '428.73  g', '429.66  g', '430.59  g', '431.52  g', '432.45  g', '433.38  g', '434.31  g', '435.24  g', '436.17  g', '437.10  g', '438.04  g', '438.98  g', '439.92  g', '440.86  g', '441.80  g', '442.74  g', '443.68  g', '444.62  g', '445.56  g', '446.50  g', '447.45  g', '448.40  g', '449.35  g', '450.30  g', '451.25  g', '452.20  g', '453.15  g', '454.10  g', '455.05  g', '456.00  g', '456.96  g', '457.92  g', '458.88  g', '459.84  g', '460.80  g', '461.76  g', '462.72  g', '463.68  g', '464.64  g', '465.60  g', '466.57  g', '467.54  g', '468.51  g', '469.48  g', '470.45  g', '471.42  g', '472.39  g', '473.36  g', '474.33  g', '475.30  g', '476.28  g', '477.26  g', '478.24  g', '479.22  g', '480.20  g', '481.18  g', '482.16  g', '483.14  g', '484.12  g', '485.10  g', '486.09  g', '487.08  g', '488.07  g', '489.06  g', '490.05  g', '491.04  g', '492.03  g', '493.02  g', '494.01  g', '495.00  g', '496.00  g', '497.00  g', '498.00  g', '499.00  g', '500.00  g', '501.00  g', '502.00  g', '503.00  g', '504.00  g', '505.00  g']

    def read_data(self, layout, serial, calculation_data, samples_data, filename, period=1, runtime=None,
                  digits_after_dec=3, logging=False):
        """
        writes data read from serial port to given file.
        assumes that this method won't be called with filename = None
        """
        thread = current_thread()
        self.layout = layout
        try:
            serial.timeout = 1
        except SerialException as e:
            raise_error(message=f'Возникла проблема с доступом к порту:{e}', layout=self.layout)

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except FileNotFoundError:
            raise_error(message="Ошибка в пути к файлу.", layout=self.layout)
            return layout.reset_layout()

        self.filename = filename
        self.digits_after_dec = digits_after_dec

        if samples_data['collect_samples']:
            self.collect_samples = True
            self.sample_data['max_volume'] = samples_data['max_sample_value']
            self.sample_data['current_sample'] = 1
            self.sample_data['start_time'] = 0
            self.sample_data['filename'] = self.filename.rstrip('.txt') + "_пробы.txt"

        if logging:
            self.log_file = open(ROOT_PATH / f'log_{datetime.date.today()}_{serial.port}', "a+")
            self.log_file.write('\n[LOG START]\n')
            serial.flushInput()
        with open(self.filename, "a+", encoding="utf-8") as file:
            file.write(f"{datetime.date.today()}  {datetime.datetime.now().strftime('%H:%M')}\n")
            file.write(
                f"Время, с  Масса, г   Разность масс, г   Поток, {'л/м2 час' if calculation_data['flow_dimension'] == 1 else 'м3/м2 час'}  Проницаемость, {'л/м2 час бар' if calculation_data['flow_dimension'] == 1 else 'м3/м2 час бар'}\n")

        last_reading = 0
        time_elapsed = layout.time_elapsed.get()

        while not getattr(thread, "stop_thread", False) and (runtime is None or time_elapsed <= runtime):
            start = time.time()
            layout.time_elapsed.set(time_elapsed)
            if self.collect_samples:
                self.update_samples_layout_data(time_elapsed)
            if getattr(thread, "start_new_sample", False):
                setattr(thread, "start_new_sample", False)
                self.handle_start_new_sample_command(time_elapsed)
            reading = self.get_reading(serial, logging=logging)
            if reading is not None:
                if self.validate_reading(reading, last_reading, calculation_data):
                    Thread(target=self.handle,
                           args=(layout, time_elapsed, reading,
                                 calculation_data, last_reading, digits_after_dec)).start()
                    last_reading = reading
                else:
                    self.interpolation_data = {'reading': reading,
                                               'time': time_elapsed}

            if time_elapsed % period == 0:
                mass, mass_difference, volume, flow, permeability = self.calculate(self.last_read['mass'], calculation_data,
                               last_reading=self.last_entry['mass'] if self.last_entry else 0)
                entry = {
                    'mass': mass,
                    'mass_difference': mass_difference,
                    'flow': flow,
                    'volume':  volume,
                    'permeability': permeability,
                }
                self.write_reading(time_elapsed, entry['mass'], entry['mass_difference'], entry['flow'], entry['permeability'])
                self.last_entry = entry
                layout.entries_made.set(layout.entries_made.get() + 1)
            time_elapsed += 1
            elapsed = time.time() - start
            time.sleep(1. - min(1., elapsed))
        time.sleep(1.)

        file = open(filename, "a+", encoding="utf-8")
        file.write('\n')
        file.close()
        if logging:
            self.log_file.write('\n[LOG END]\n')
            self.log_file.close()

    def get_reading(self, serial, logging=False):
        try:
            if self.debug:
                buffer = '\n'
                reading = self.get_debug_reading()
            else:
                buffer = serial.read(serial.in_waiting).decode()
                reading = serial.readline().decode()
        except OSError:
            raise_error("Потеряна связь с весами", "Потеряна связь с весами. Проверьте подключение и запустите программу снова", layout=self.layout)
            current_thread().stop_thread = True
            self.layout.reset_layout()
        except UnicodeDecodeError as e:
            raise_error("Ошибка обработки", f"Возникла ошибка при обработке данных. {e}", layout=self.layout)
            current_thread().stop_thread = True
            self.layout.reset_layout()

        if not buffer.endswith('\n'):
            if '\n' in buffer:
                split_buffer = buffer.split('\n')
                last_string = split_buffer[-1]
                buffer = split_buffer[:-1]
            else:
                last_string = buffer
                buffer = ''
            reading = last_string + reading
        reading = reading or '-  0.00  g  !\r\n'
        if logging:
            self.write_log(data=buffer + reading)
        try:
            reading = re.search(r'(\d+\.\d+)', reading).group(1)
            reading = float(reading.rstrip(' ').rstrip('g'))
        except ValueError:
            reading = None
        except AttributeError:
            reading = self.get_reading(serial)
        return reading

    def validate_reading(self, reading, last_reading, calculation_data):
        diff = reading - last_reading if not self.interpolation_data else reading - self.interpolation_data['reading']
        if diff < 0 and abs(diff / last_reading) * 100 > calculation_data['percent']:
            return False
        return True

    def handle(self, layout, now, reading, calculation_data, last_reading=None, digits_after_dec=2):
        if self.interpolation_data:
            mass, mass_difference, volume, flow, permeability = self.calculate(reading, calculation_data,
                                                                               last_reading=self.interpolation_data[
                                                                                     'reading'])
            (inter_mass, inter_diff, inter_volume,
             inter_flow, inter_perm) = self.calculate(self.interpolation_data['reading'], calculation_data,
                                                      last_reading=last_reading,
                                                      interpolate=True,
                                                      prev_diff=self.last_read['mass_difference'],
                                                      next_diff=mass_difference)

            self.write_reading(self.interpolation_data['time'], inter_mass, inter_diff, inter_flow, inter_perm)
            layout.entries_made.set(layout.entries_made.get() + 1)
            self.interpolation_data = None
        else:
            mass, mass_difference, volume, flow, permeability = self.calculate(reading, calculation_data,
                                                                               last_reading=last_reading)
        self.last_read = {
            'mass': mass,
            'mass_difference': mass_difference,
            'volume': volume,
            'flow': flow,
            'permeability': permeability
        }

        if self.collect_samples:
            self.handle_samples(now)

    def calculate(self, reading, calculation_data, last_reading=0.0, interpolate=False, prev_diff=None, next_diff=None):
        if interpolate:
            mass_difference = (prev_diff + next_diff) / 2
        else:
            mass_difference = reading - last_reading if last_reading is not None else 0
        volume = (mass_difference / 1000 / calculation_data['density']) / calculation_data['interval']
        flow = volume * 3600 / calculation_data['surface'] * 1000
        flow = flow / calculation_data['flow_dimension']
        permeability = flow / calculation_data['difference']
        return reading, mass_difference, volume, flow, permeability

    def write_log(self, data):
        self.log_file.write(data)
        self.log_file.flush()

    def write_reading(self, current_time, mass, mass_difference, flow, permeability):
        with open(self.filename, "a+", encoding="utf-8") as file:
            file.write(
                f"{current_time}  {mass:.{self.digits_after_dec}f}  {mass_difference:.{self.digits_after_dec}f}  {flow:.{self.digits_after_dec}f}  {permeability:.{self.digits_after_dec}f}\n")

    def new_sample(self, time_elapsed):
        sample_data = self.sample_data
        if sample_data['current_sample'] == 1:
            file = open(sample_data['filename'], "a+", encoding="utf-8")
            file.write(f"{datetime.date.today()}  {datetime.datetime.now().strftime('%H:%M')}\n")
            file.write(
                f"Номер пробы; Время начала сбора пробы, сек; Время конца сбора пробы, сек; Объем пробы, мл\n")
            file.close()
        file = open(sample_data['filename'], "a+", encoding="utf-8")
        file.write(f"{sample_data['current_sample']}  "
                   f"{sample_data['start_time']}  "
                   f"{time_elapsed}  "
                   f"{sample_data['current_volume']:.{self.digits_after_dec}f}\n")
        file.flush()
        file.close()
        self.sample_data['current_sample'] += 1
        self.sample_data['current_volume'] = 0.0
        self.sample_data['start_time'] = time_elapsed
        self.sample_data['continue_sample'] = False
        self.update_samples_layout_data(time_elapsed)

    def handle_samples(self, time_elapsed):
        self.sample_data['current_volume'] += self.last_read['mass_difference']
        if not self.sample_data['continue_sample']:
            if self.sample_data['current_volume'] >= self.sample_data['max_volume']:
                Thread(target=self.handle_sample_max_volume_reached,
                       args=[time_elapsed]).start()

    def handle_start_new_sample_command(self, time_elapsed):
        self.new_sample(time_elapsed)

    def handle_sample_max_volume_reached(self, time_elapsed):
        self.sample_data['continue_sample'] = True
        messagebox_answer = sample_max_volume_reached_mb(self.sample_data['max_volume'], self.sample_data['current_sample'], self.layout)
        if messagebox_answer:
            self.new_sample(self.layout.time_elapsed.get())

    def update_samples_layout_data(self, time_elapsed):
        self.layout.current_sample.set(self.sample_data['current_sample'])
        self.layout.sample_time_elapsed.set(time_elapsed - self.sample_data['start_time'])
        self.layout.sample_value.set(self.sample_data['current_volume'])

    def get_debug_reading(self):
        # DEBUG LIST GENERATOR
        # for i in range(0, 100):
        #     if i == 0:
        #         list = []
        #         last_value = 0.00
        #     value = last_value + (1 + i // 10) * 0.01
        #     list.append(f'{value:.2f}  g')
        #     last_value = value
        if self.reading_list:
            return self.reading_list.pop(0)
        return "-  0.00  g  !\r\n"
