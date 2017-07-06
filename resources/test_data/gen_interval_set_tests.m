
ts_max = 10000000000;
t1 = [0]*ones(1, 3);
t2 = [ts_max]*ones(1, 3);
for i = 1
    a1 = int64(t1(i) + sort(rand(1000, 1) * (t2(i)-t1(i))));
    b1 = int64(t1(i) + sort(rand(1200, 1) * (t2(i)-t1(i))));   
    int1 = intervalSet(a1, b1, '-fixit');
    a_i1 = Start(int1);
    b_i1 = End(int1);
    
    a2 = int64(t1(i) + sort(rand(300, 1) * (t2(i)-t1(i))));
    b2 = int64(t1(i) + sort(rand(400, 1) * (t2(i)-t1(i))));   
    int2 = intervalSet(a2, b2, '-fixit');
    a_i2 = Start(int2);
    b_i2 = End(int2);
    
    int_union = union(int1, int2);
    a_union = Start(int_union);
    b_union = End(int_union);
    
    int_intersect = intersect(int1, int2);
    a_intersect = Start(int_intersect);
    b_intersect = End(int_intersect);
    
    int_diff1 = diff(int1, int2);
    a_diff1 = Start(int_diff1);
    b_diff1 = End(int_diff1);
    
    int_diff2 = diff(int2, int1);
    a_diff2 = Start(int_diff2);
    b_diff2 = End(int_diff2);
    
    t = int64(sort(rand(10000, 1) * ts_max));
    d = randn(size(t));
    tsd_1 = tsd(t, d);
    
    tsd_r1 = Restrict(tsd_1, int1);
    t_r1 = Range(tsd_r1, 'ts');
    d_r1 = Data(tsd_r1);
    
    tsd_r2 = Restrict(tsd_1, int2);
    t_r2 = Range(tsd_r2, 'ts');
    d_r2 = Data(tsd_r2);
    
    int1_drop = dropShortIntervals(int1, 0.5e7);
    a_i1_drop = Start(int1_drop);
    b_i1_drop = End(int1_drop);
    
    save(['/Users/fpbatta/src/batlab/neuroseries/resources/test_data/interval_set_data_', mat2str(i)], 'a*', 'b*', 't*', 'd*');
    
end
