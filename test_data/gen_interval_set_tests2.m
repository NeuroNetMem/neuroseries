
ts_max = 10000000;
t1 = [0]*ones(1, 3);
t2 = [ts_max]*ones(1, 3);
for i = 1
    a1 = int64(t1(i) + sort(rand(1000, 1) * (t2(i)-t1(i))));
    b1 = int64(t1(i) + sort(rand(1200, 1) * (t2(i)-t1(i))));   
    int1 = intervalSet(double(a1), double(b1), '-fixit');
    a_i1 = Start(int1);
    b_i1 = End(int1);
    
    a2 = int64(t1(i) + sort(rand(300, 1) * (t2(i)-t1(i))));
    b2 = int64(t1(i) + sort(rand(400, 1) * (t2(i)-t1(i))));   
    int2 = intervalSet(double(a2), double(b2), '-fixit');
    a_i2 = Start(int2);
    b_i2 = End(int2);
    
    int1_drop = dropShortIntervals(int1, 2e3);
    a_i1_drop = Start(int1_drop);
    b_i1_drop = End(int1_drop);
    
    int1_merge = mergeCloseIntervals(int1, 3e3);
    a_i1_merge = Start(int1_merge);
    b_i1_merge = End(int1_merge);
    
    save(['/Users/fpbatta/src/batlab/neuroseries/resources/test_data/interval_set_data_dropmerge', mat2str(i)], 'a*', 'b*', 't*');
    
end
